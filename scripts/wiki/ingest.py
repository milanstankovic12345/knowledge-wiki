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
from scripts.extractors.pdf import PAGE_MARKER, PAGE_MARKER_RE, extract_pdf
from scripts.models import Analysis, SourceDoc
from scripts.providers.base import ProviderUnavailable, TextProvider
from scripts.providers.router import select_provider
from scripts.security import validate_raw_path, wrap_untrusted
from scripts.storage import dump_frontmatter, parse_frontmatter, sha256_file, slugify
from scripts.wiki.index import add_index_entry, append_log, set_health
from scripts.wiki.integrate import (
    integrate_topics,
    topic_slugs,
    write_book_page,
    write_source_summary,
)

SYSTEM_PROMPT = (
    "You analyse a source document for a personal knowledge wiki. "
    "Respond only with JSON matching the schema. Be faithful to the text; "
    "do not add facts that are not in it. 'concepts' are short noun phrases "
    "(1-4 words) suitable as wiki topic titles. Markers like <!-- page: 12 --> give "
    "source page numbers; end a claim with (p. N) when you can tell its page. "
    "Summarise in your own words; never copy long passages."
)
FOLDER_TYPES = {"articles": "article", "books": "book"}
JSON_ATTEMPTS = 2

ProviderFactory = Callable[[Vault, str, str, str], TextProvider]


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


def _author(value: Any) -> str:
    """Clipper writes `author` as a list of `[[Name]]` wikilinks; store plain names."""
    items = value if isinstance(value, list) else [value]
    names = [re.sub(r"\[\[|\]\]", "", str(i)).strip() for i in items if i]
    return ", ".join(n for n in names if n)


def parse_source(
    vault: Vault, path: Path, content_hash: str, converter: Any | None = None
) -> SourceDoc:
    pages, low = 0, []
    if path.suffix.lower() == ".pdf":
        extraction = extract_pdf(path, converter)
        meta = {"title": extraction.title, "author": extraction.author}
        meta["captured_at"] = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        body, pages, low = (
            extraction.markdown,
            extraction.page_count,
            extraction.low_confidence_pages,
        )
    else:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    rel = path.relative_to(vault.root.resolve()).as_posix()
    source_type = str(meta.get("source_type") or FOLDER_TYPES.get(path.parent.name, "article"))
    classes = vault.privacy.get("classifications", {})
    declared = str(meta.get("privacy") or "")
    default = vault.privacy.get("source_defaults", {}).get(
        source_type, vault.privacy.get("default_classification", "private")
    )
    return SourceDoc(
        raw_path=rel,
        source_type=source_type,
        title=str(meta.get("title") or path.stem),
        author=_author(meta.get("author")),
        source_url=str(meta.get("source_url") or meta.get("source") or ""),
        captured_at=str(meta.get("captured_at") or meta.get("created") or ""),
        content_hash=content_hash,
        privacy=declared if declared in classes else str(default),
        body=body.strip(),
        page_count=pages,
        low_confidence_pages=low,
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


def _with_page_context(chunks: list[str]) -> list[str]:
    """Keep page numbers usable: a chunk that starts mid-page gets the current marker."""
    page, out = None, []
    for chunk in chunks:
        if page and not chunk.lstrip().startswith("<!-- page:"):
            chunk = f"{PAGE_MARKER.format(n=page)}\n\n{chunk}"
        found = PAGE_MARKER_RE.findall(chunk)
        page = found[-1] if found else page
        out.append(chunk)
    return out


def analyse(provider: TextProvider, body: str, limit: int) -> Analysis:
    schema = Analysis.model_json_schema()
    schema["required"] = list(schema["properties"])  # defaults would let the model skip fields
    result: Analysis | None = None
    for chunk in _with_page_context(chunk_text(body, limit)):
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
) -> IngestResult:
    allowed = set(vault.settings["allowed_extensions"]["document"])
    path = validate_raw_path(candidate, vault.root, allowed)
    content_hash = sha256_file(path)
    own_session = session is None
    db = session or open_db(vault.path("database"))
    try:
        known = find_by_hash(db, content_hash)
        if known and known.status == "done":
            return IngestResult("duplicate", known.summary_path)

        doc = parse_source(vault, path, content_hash, converter)
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
            result = _run(vault, doc, provider_factory)
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


def _run(vault: Vault, doc: SourceDoc, provider_factory: ProviderFactory) -> IngestResult:
    provider = provider_factory(vault, doc.privacy, doc.source_type, doc.raw_path)
    limit = int(vault.settings.get("models", {}).get("context_chars", 24000))
    analysis = analyse(provider, doc.body, limit)

    now = _now()
    stamp, today = now.isoformat(timespec="seconds"), now.date().isoformat()
    slug = _unique_slug(vault, doc.title, doc.content_hash)

    # Pass 1 output: deterministic extraction, written once and never rewritten by the LLM.
    processed = vault.root / "processed" / "documents" / f"{slug}.md"
    if not processed.exists():
        meta = {"raw_path": doc.raw_path, "content_hash": doc.content_hash, "title": doc.title}
        if doc.page_count:
            meta |= {"page_count": doc.page_count, "low_confidence_pages": doc.low_confidence_pages}
        processed.write_text(dump_frontmatter(meta, doc.body + "\n"), encoding="utf-8")
    processed_rel = processed.relative_to(vault.root).as_posix()

    # Pass 2: LLM integration.
    slugs = topic_slugs(analysis)
    review = [
        f"Little or no text extracted on page {n}; check OCR/layout against the raw PDF."
        for n in doc.low_confidence_pages
    ]
    summary = write_source_summary(
        vault, doc, analysis, slug, slugs, processed_rel, provider.name, provider.model, stamp,
        review,
    )  # fmt: skip
    book = None
    if doc.source_type == "book":
        book = write_book_page(vault, doc, analysis, slug, slugs, processed_rel, stamp, today)
    created, updated = integrate_topics(vault, doc, analysis, slug, today)

    index = vault.root / "index.md"
    if book:
        add_index_entry(index, "Books", f"books/{book.stem}", doc.title)
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
