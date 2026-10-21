"""Shared ingestion workflow for one Markdown/text source."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from scripts.config import Vault
from scripts.database import Job, Source, find_by_hash, open_db
from scripts.extractors.article import clean_author, extract_article
from scripts.extractors.audio import Transcriber, transcribe
from scripts.extractors.image import describe_images, prepare_images
from scripts.extractors.pdf import extract_pdf
from scripts.extractors.video import Frame, describe_frames, extract_video
from scripts.models import Analysis, FrameRef, SourceDoc
from scripts.providers.base import ProviderUnavailable, TextProvider
from scripts.providers.router import select_provider, select_vision_provider
from scripts.providers.vision import VisionProvider
from scripts.security import validate_raw_dir, validate_raw_path, wrap_untrusted
from scripts.storage import dump_frontmatter, parse_frontmatter, sha256_file, slugify
from scripts.wiki.index import add_index_entry, append_log, set_health
from scripts.wiki.integrate import (
    integrate_topics,
    topic_slugs,
    write_book_page,
    write_source_summary,
    write_video_page,
)

SYSTEM_PROMPT = (
    "You analyse a source document for a personal knowledge wiki. "
    "Respond only with JSON matching the schema. Be faithful to the text; "
    "do not add facts that are not in it. 'concepts' are short noun phrases "
    "(1-4 words) suitable as wiki topic titles. Markers like <!-- page: 12 --> give "
    "source page numbers; end a claim with (p. N) when you can tell its page. Markers like "
    "<!-- t: 03:20 --> give a position in a transcribed recording; end a claim with (t. 03:20) "
    "when you can tell where it was said. Markers like <!-- image: 2 --> number the images of a "
    "photo set in order; end a claim with (img. 2) when it comes from one image. "
    "Summarise in your own words; never copy long passages."
)
FOLDER_TYPES = {
    "articles": "article",
    "books": "book",
    "telegram": "telegram_document",
    "youtube": "youtube",
}
MEDIA_TYPES = {  # default source type by media kind
    "audio": "telegram_voice",
    "video": "pc_video",
    "image": "telegram_photo",
}
MARKER_LINE = re.compile(r"^<!-- (?:page|t|image): [^>]+ -->$", re.MULTILINE)
URL_IN_TEXT = re.compile(r"https?://[^\s<>\"')]+")
JSON_ATTEMPTS = 2

ProviderFactory = Callable[[Vault, str, str, str], TextProvider]
VisionFactory = Callable[[Vault, str, str, str], VisionProvider]


class IngestError(RuntimeError):
    pass


@dataclass
class IngestResult:
    status: str  # "ingested" | "duplicate"
    summary_path: str
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    book_path: str = ""
    needs_review: list[str] = field(default_factory=list)
    job_id: int = 0


def _now() -> datetime:
    return datetime.now(UTC).astimezone()


VISIBILITY_CLASSES = {"private": "personal", "public": "public"}


def resolve_privacy(config: dict[str, Any], meta: dict[str, Any], source_type: str) -> str:
    """Privacy class: explicit `privacy`, else clipper `visibility`, else the type default.

    `visibility: private` tightens an article to `personal`. `visibility: public` never loosens a
    type that requires explicit cloud approval, and an unknown value falls back to the default.
    """
    classes = config.get("classifications", {})
    default = str(
        config.get("source_defaults", {}).get(
            source_type, config.get("default_classification", "private")
        )
    )
    declared = str(meta.get("privacy") or "")
    if declared in classes:
        return declared
    mapped = VISIBILITY_CLASSES.get(str(meta.get("visibility") or "").strip().lower(), "")
    if mapped == "public" and source_type in config.get("cloud_requires_explicit_approval", []):
        return default
    return mapped if mapped in classes else default


def _media_kind(vault: Vault, path: Path) -> str:
    ext = path.suffix.lower()
    for kind in ("audio", "video", "image"):
        if ext in vault.settings["allowed_extensions"][kind]:
            return kind
    return ""


def _caption_details(caption: str, fallback_title: str) -> tuple[str, str, str]:
    """(title, source_url, body) from a user-supplied caption; the caption is untrusted content."""
    first = caption.strip().splitlines()[0] if caption.strip() else ""
    url = URL_IN_TEXT.search(caption)
    title = URL_IN_TEXT.sub("", first).strip()[:80] or fallback_title
    body = f"## Caption\n\n{caption.strip()}" if caption.strip() else ""
    return title, url.group(0) if url else "", body


def _image_doc(
    vault: Vault,
    raw_rel: str,
    sources: list[Path],
    stem: str,
    content_hash: str,
    caption: str,
    fallback_title: str,
    captured_at: str,
    url: str = "",
) -> SourceDoc:
    """Image sources have no text of their own: the body is the caption, the vision model adds
    descriptions later. Only metadata-free copies of the images are ever shown to a model."""
    images = prepare_images(vault, sources, stem)
    title, caption_url, body = _caption_details(caption, fallback_title)
    source_url = url or caption_url
    source_type = "instagram" if "instagram.com/" in source_url else "telegram_photo"
    return SourceDoc(
        raw_path=raw_rel,
        source_type=source_type,
        title=title,
        source_url=source_url,
        captured_at=captured_at,
        content_hash=content_hash,
        privacy=resolve_privacy(vault.privacy, {}, source_type),
        body=body,
        media_kind="image",
        frames=[FrameRef(path=r, time=str(n)) for n, r in enumerate(images, start=1)],
    )


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def parse_source(
    vault: Vault,
    path: Path,
    content_hash: str,
    converter: Any | None = None,
    transcriber: Transcriber | None = None,
) -> SourceDoc:
    pages, low = 0, []
    media: dict[str, Any] = {}
    kind = _media_kind(vault, path)
    if kind == "image":
        stem = f"{slugify(path.stem)}-{content_hash[:8]}"
        rel = path.relative_to(vault.root.resolve()).as_posix()
        captured = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        caption = read_text_if_exists(path.with_suffix(".caption.txt"))
        return _image_doc(vault, rel, [path], stem, content_hash, caption, path.stem, captured)
    if kind:
        stem = f"{slugify(path.stem)}-{content_hash[:8]}"
        meta = {"title": path.stem}
        meta["captured_at"] = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        if kind == "video":
            video = extract_video(path, vault, stem, transcriber)
            transcript, frames = video.transcript, video.frames
            duration = video.duration
        else:
            transcript, frames, duration = transcribe(path, vault, stem, transcriber), [], 0.0
        body = transcript.markdown
        media = {
            "media_kind": kind,
            "duration_seconds": duration or transcript.duration,
            "language": transcript.language,
            "extraction_model": transcript.model,
            "processed_paths": list(transcript.paths),
            "frames": [FrameRef(path=f.path, time=f.time) for f in frames],
            "review_notes": list(transcript.review),
        }
    elif path.suffix.lower() == ".pdf":
        extraction = extract_pdf(path, converter)
        meta = {"title": extraction.title, "author": extraction.author}
        meta["captured_at"] = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        body, pages, low = (
            extraction.markdown,
            extraction.page_count,
            extraction.low_confidence_pages,
        )
    elif path.parent.name == "articles" and path.suffix.lower() in (".md", ".txt"):
        article = extract_article(path.read_text(encoding="utf-8"), path)
        meta = {
            **(article.meta or {}),
            "title": article.title,
            "author": article.author,
            "source_url": article.source_url,
            "captured_at": article.captured_at,
        }
        body = article.markdown
    else:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    rel = path.relative_to(vault.root.resolve()).as_posix()
    default_type = MEDIA_TYPES.get(kind) or FOLDER_TYPES.get(path.parent.name, "article")
    source_type = str(meta.get("source_type") or default_type)
    return SourceDoc(
        raw_path=rel,
        source_type=source_type,
        title=str(meta.get("title") or path.stem),
        author=clean_author(meta.get("author")),
        source_url=str(meta.get("source_url") or meta.get("source") or ""),
        captured_at=str(meta.get("captured_at") or meta.get("created") or ""),
        content_hash=content_hash,
        privacy=resolve_privacy(vault.privacy, meta, source_type),
        body=body.strip(),
        page_count=pages,
        low_confidence_pages=low,
        **media,
    )


def chunk_text(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        while len(para) > limit:  # hard-split an oversized paragraph
            if current:
                chunks.append(current)
                current = ""
            chunks.append(para[:limit])
            para = para[limit:]
        if current and len(current) + len(para) + 2 > limit:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks or [""]


def _with_marker_context(chunks: list[str]) -> list[str]:
    """Keep positions usable: a chunk that starts mid-source gets the current page/time marker."""
    marker, out = None, []
    for chunk in chunks:
        if marker and not chunk.lstrip().startswith("<!-- "):
            chunk = f"{marker}\n\n{chunk}"
        found = MARKER_LINE.findall(chunk)
        marker = found[-1] if found else marker
        out.append(chunk)
    return out


def analyse(provider: TextProvider, body: str, limit: int) -> Analysis:
    schema = Analysis.model_json_schema()
    schema["required"] = list(schema["properties"])  # defaults would let the model skip fields
    result: Analysis | None = None
    for chunk in _with_marker_context(chunk_text(body, limit)):
        part = None
        for _ in range(JSON_ATTEMPTS):
            raw = provider.generate(SYSTEM_PROMPT, wrap_untrusted(chunk), schema)
            try:
                part = Analysis.model_validate_json(raw)
                break
            except ValidationError:
                continue
        if part is None:
            raise IngestError("model returned invalid JSON")
        result = part if result is None else result.merge(part)
    return result or Analysis()


def _unique_slug(vault: Vault, title: str, content_hash: str) -> str:
    slug = slugify(title)
    existing = vault.root / "wiki" / "sources" / f"{slug}.md"
    if existing.exists():
        meta, _ = parse_frontmatter(existing.read_text("utf-8"))
        if meta.get("content_hash") != content_hash:
            return f"{slug}-{content_hash[:8]}"
    return slug


def ingest_file(
    vault: Vault,
    candidate: str | Path,
    provider_factory: ProviderFactory = select_provider,
    session: Session | None = None,
    converter: Any | None = None,
    transcriber: Transcriber | None = None,
    vision_factory: VisionFactory = select_vision_provider,
    on_job: Callable[[int], None] | None = None,
) -> IngestResult:
    exts = vault.settings["allowed_extensions"]
    allowed = {e for kind in ("document", "audio", "video", "image") for e in exts[kind]}
    path = validate_raw_path(candidate, vault.root, allowed)
    return _ingest(
        vault,
        sha256_file(path),
        path.name,
        lambda content_hash: parse_source(vault, path, content_hash, converter, transcriber),
        provider_factory,
        session,
        vision_factory,
        on_job,
    )


def ingest_carousel(
    vault: Vault,
    folder: str | Path,
    provider_factory: ProviderFactory = select_provider,
    session: Session | None = None,
    vision_factory: VisionFactory = select_vision_provider,
    on_job: Callable[[int], None] | None = None,
) -> IngestResult:
    """Ingest an ordered image set (`001.jpg`, `002.jpg`, ...) as one source.

    The content hash covers the member hashes in order, so the same images in a different order
    are a different carousel. `caption.txt` and `original-url.txt` are optional.
    """
    directory = validate_raw_dir(folder, vault.root)
    image_exts = set(vault.settings["allowed_extensions"]["image"])
    members = sorted(p for p in directory.iterdir() if p.suffix.lower() in image_exts)
    if not members:
        raise IngestError("carousel folder contains no images")
    for member in members:
        validate_raw_path(member, vault.root, image_exts)
    joined = "\n".join(sha256_file(m) for m in members)
    content_hash = hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def build(content_hash: str) -> SourceDoc:
        stem = f"{slugify(directory.name)}-{content_hash[:8]}"
        rel = directory.relative_to(vault.root.resolve()).as_posix()
        captured = datetime.fromtimestamp(directory.stat().st_mtime).date().isoformat()
        return _image_doc(
            vault,
            rel,
            members,
            stem,
            content_hash,
            read_text_if_exists(directory / "caption.txt"),
            f"Carousel {directory.name}",
            captured,
            read_text_if_exists(directory / "original-url.txt"),
        )

    return _ingest(
        vault,
        content_hash,
        directory.name,
        build,
        provider_factory,
        session,
        vision_factory,
        on_job,
    )


def _ingest(
    vault: Vault,
    content_hash: str,
    original_name: str,
    make_doc: Callable[[str], SourceDoc],
    provider_factory: ProviderFactory,
    session: Session | None,
    vision_factory: VisionFactory,
    on_job: Callable[[int], None] | None,
) -> IngestResult:
    own_session = session is None
    db = session or open_db(vault.path("database"))
    try:
        known = find_by_hash(db, content_hash)
        if known and known.status == "done":
            return IngestResult("duplicate", known.summary_path)

        doc = make_doc(content_hash)
        if known is None:
            known = Source(
                content_hash=content_hash,
                source_type=doc.source_type,
                original_name=original_name,
                source_url=doc.source_url,
                raw_path=doc.raw_path,
                privacy=doc.privacy,
                captured_at=doc.captured_at,
            )
            db.add(known)
            db.flush()
        job = Job(source_id=known.id, operation="ingest", status="running", started_at=_now())
        db.add(job)
        db.commit()
        if on_job:
            on_job(job.id)

        try:
            result = _run(vault, doc, provider_factory, vision_factory)
        except (IngestError, ProviderUnavailable, PermissionError, OSError) as exc:
            job.status, job.error_message = "failed", str(exc)
            known.status = "failed"
            db.commit()
            raise
        known.status, known.summary_path = "done", result.summary_path
        db.refresh(job)
        if job.status != "cancelled":  # /cancel on a running job is final
            job.status = "done"
        job.completed_at = _now()
        db.commit()
        result.job_id = job.id
        return result
    finally:
        if own_session:
            db.close()


def _frame_descriptions(
    vault: Vault, doc: SourceDoc, vision_factory: VisionFactory
) -> tuple[str, list[str], list[str]]:
    """Describe sampled video frames. Returns (body addition, processed paths, review notes).

    If the local vision model is unavailable nothing is invented: the frames stay on disk and
    the summary is flagged. Cloud-blocked requests still raise.
    """
    if not doc.frames:
        return "", [], []
    if doc.media_kind == "image":
        # An image source has nothing else to summarise, so a missing vision model fails the
        # job (retryable) rather than inventing a description.
        vision = vision_factory(vault, doc.privacy, doc.source_type, doc.raw_path)
        stem = f"{slugify(Path(doc.raw_path).stem)}-{doc.content_hash[:8]}"
        text, path = describe_images(vault, [f.path for f in doc.frames], stem, vision)
        return f"\n\n## Image descriptions\n\n{text}", [path], []
    try:
        vision = vision_factory(vault, doc.privacy, doc.source_type, doc.raw_path)
    except ProviderUnavailable:
        note = (
            f"Frame descriptions pending: vision model unavailable; {len(doc.frames)} sampled "
            "frames are kept under processed/image-descriptions/."
        )
        return "", [], [note]
    frames = [Frame(f.path, f.time) for f in doc.frames]
    stem = Path(doc.processed_paths[0]).stem
    text, path = describe_frames(vault, frames, stem, vision)
    return f"\n\n## Frame descriptions\n\n{text}", [path], []


def _run(
    vault: Vault, doc: SourceDoc, provider_factory: ProviderFactory, vision_factory: VisionFactory
) -> IngestResult:
    provider = provider_factory(vault, doc.privacy, doc.source_type, doc.raw_path)
    limit = int(vault.settings.get("models", {}).get("context_chars", 24000))
    extra, frame_paths, frame_notes = _frame_descriptions(vault, doc, vision_factory)
    analysis = analyse(provider, doc.body + extra, limit)

    now = _now()
    stamp, today = now.isoformat(timespec="seconds"), now.date().isoformat()
    slug = _unique_slug(vault, doc.title, doc.content_hash)

    # Pass 1 output: deterministic extraction, written once and never rewritten by the LLM.
    if doc.media_kind:  # transcripts/frame descriptions were already written during extraction
        processed_rels = [*doc.processed_paths, *frame_paths]
    else:
        processed = vault.root / "processed" / "documents" / f"{slug}.md"
        if not processed.exists():
            meta = {"raw_path": doc.raw_path, "content_hash": doc.content_hash, "title": doc.title}
            if doc.page_count:
                meta |= {
                    "page_count": doc.page_count,
                    "low_confidence_pages": doc.low_confidence_pages,
                }
            processed.write_text(dump_frontmatter(meta, doc.body + "\n"), encoding="utf-8")
        processed_rels = [processed.relative_to(vault.root).as_posix()]

    # Pass 2: LLM integration.
    slugs = topic_slugs(analysis)
    review = (
        [
            f"Little or no text extracted on page {n}; check OCR/layout against the raw PDF."
            for n in doc.low_confidence_pages
        ]
        + doc.review_notes
        + frame_notes
    )
    summary = write_source_summary(
        vault, doc, analysis, slug, slugs, processed_rels, provider.name, provider.model, stamp,
        review,
    )  # fmt: skip
    book = video = None
    if doc.source_type == "book":
        book = write_book_page(vault, doc, analysis, slug, slugs, processed_rels[0], stamp, today)
    elif doc.media_kind == "video":
        video = write_video_page(vault, doc, analysis, slug, slugs, processed_rels, review)
    created, updated = integrate_topics(vault, doc, analysis, slug, today)

    index = vault.root / "index.md"
    if book:
        add_index_entry(index, "Books", f"books/{book.stem}", doc.title)
    elif video:
        add_index_entry(index, "Videos", f"videos/{video.stem}", doc.title)
    elif doc.media_kind == "image":
        add_index_entry(index, "Photos", f"sources/{slug}", doc.title)
    elif doc.media_kind:
        add_index_entry(index, "Videos", f"sources/{slug}", f"{doc.title} (audio)")
    elif doc.source_type == "youtube":
        add_index_entry(index, "Videos", f"sources/{slug}", doc.title)
    else:
        add_index_entry(index, "Articles", f"sources/{slug}", doc.title)
    by_slug = {slugify(c): c for c in analysis.concepts}
    for new in created:
        add_index_entry(index, "Topics", f"topics/{new}", by_slug.get(new, new))
    set_health(index, "Last ingest", stamp)

    append_log(
        vault.root / "log.md",
        f"[{now.strftime('%Y-%m-%d %H:%M')}] ingest | {doc.title}",
        {
            "Source type": doc.source_type,
            "Raw path": doc.raw_path,
            "Content hash": doc.content_hash,
            "Provider": provider.name,
            "Model": provider.model,
            "Pages created": json.dumps(
                [f"wiki/sources/{slug}.md"]
                + ([f"wiki/books/{book.stem}.md"] if book else [])
                + ([f"wiki/videos/{video.stem}.md"] if video else [])
                + [f"wiki/topics/{c}.md" for c in created]
            ),
            "Pages updated": json.dumps([f"wiki/topics/{u}.md" for u in updated] + ["index.md"]),
            "Contradictions": "none recorded",
            "Human review": "pending",
        },
    )
    return IngestResult(
        "ingested",
        summary.relative_to(vault.root).as_posix(),
        created=created,
        updated=updated,
        book_path=book.relative_to(vault.root).as_posix() if book else "",
        needs_review=review,
    )
