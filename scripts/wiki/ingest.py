"""Shared ingestion workflow for one Markdown/text source."""

from __future__ import annotations

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
from scripts.extractors.pdf import extract_pdf
from scripts.extractors.video import Frame, describe_frames, extract_video
from scripts.models import Analysis, FrameRef, SourceDoc
from scripts.providers.base import ProviderUnavailable, TextProvider
from scripts.providers.router import select_provider, select_vision_provider
from scripts.providers.vision import VisionProvider
from scripts.security import validate_raw_path, wrap_untrusted
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
    "when you can tell where it was said. "
    "Summarise in your own words; never copy long passages."
)
FOLDER_TYPES = {"articles": "article", "books": "book"}
MEDIA_TYPES = {"audio": "telegram_voice", "video": "pc_video"}  # default source type by media kind
MARKER_LINE = re.compile(r"^<!-- (?:page|t): [^>]+ -->$", re.MULTILINE)
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
    for kind in ("audio", "video"):
        if ext in vault.settings["allowed_extensions"][kind]:
            return kind
    return ""


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
) -> IngestResult:
    exts = vault.settings["allowed_extensions"]
    allowed = {e for kind in ("document", "audio", "video") for e in exts[kind]}
    path = validate_raw_path(candidate, vault.root, allowed)
    content_hash = sha256_file(path)
    own_session = session is None
    db = session or open_db(vault.path("database"))
    try:
        known = find_by_hash(db, content_hash)
        if known and known.status == "done":
            return IngestResult("duplicate", known.summary_path)

        doc = parse_source(vault, path, content_hash, converter, transcriber)
        if known is None:
            known = Source(
                content_hash=content_hash,
                source_type=doc.source_type,
                original_name=path.name,
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

        try:
            result = _run(vault, doc, provider_factory, vision_factory)
        except (IngestError, ProviderUnavailable, PermissionError, OSError) as exc:
            job.status, job.error_message = "failed", str(exc)
            known.status = "failed"
            db.commit()
            raise
        known.status, known.summary_path = "done", result.summary_path
        job.status, job.completed_at = "done", _now()
        db.commit()
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
    elif doc.media_kind:
        add_index_entry(index, "Videos", f"sources/{slug}", f"{doc.title} (audio)")
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
