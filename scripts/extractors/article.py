"""Deterministic extraction for Obsidian Web Clipper articles (no LLM, no network)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.storage import parse_frontmatter

HTML_BLOCKS = re.compile(r"<(script|style)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
HTML_COMMENTS = re.compile(r"<!--.*?-->", re.DOTALL)
IMAGE_ONLY = re.compile(
    r"^\s*!\[[^\]]*\]\([^)]*\)\s*$"  # ![alt](src)
    r"|^\s*\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)\s*$"  # [![alt](src)](link)
    r"|^\s*<img\b[^>]*>\s*$",
    re.IGNORECASE,
)
BLANK_RUNS = re.compile(r"\n{3,}")
H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
METADATA_BULLET = re.compile(
    r"^-[ \t]*(URL|Author|Captured):[ \t]*(\S[^\n]*?)[ \t]*$", re.MULTILINE
)


@dataclass
class ArticleExtraction:
    markdown: str
    title: str = ""
    author: str = ""
    source_url: str = ""
    captured_at: str = ""
    published_at: str = ""
    meta: dict[str, Any] | None = None


def clean_author(value: Any) -> str:
    """Clipper writes `author` as a list of `[[Name]]` wikilinks; store plain names."""
    items = value if isinstance(value, list) else [value]
    names = [re.sub(r"\[\[|\]\]", "", str(i)).strip() for i in items if i]
    return ", ".join(n for n in names if n)


def strip_noise(body: str) -> str:
    """Drop scripts, comments and image-only lines. Prose is never rewritten."""
    body = HTML_COMMENTS.sub("", HTML_BLOCKS.sub("", body))
    lines = [line for line in body.splitlines() if not IMAGE_ONLY.match(line)]
    return BLANK_RUNS.sub("\n\n", "\n".join(lines)).strip()


def extract_article(text: str, path: Path) -> ArticleExtraction:
    meta, body = parse_frontmatter(text)
    body = strip_noise(body)
    bullets = {k.lower(): v for k, v in METADATA_BULLET.findall(body)}
    heading = H1.search(body)
    return ArticleExtraction(
        markdown=body,
        title=str(meta.get("title") or (heading.group(1) if heading else "") or path.stem),
        author=clean_author(meta.get("author")) or bullets.get("author", ""),
        source_url=str(meta.get("source_url") or meta.get("source") or bullets.get("url", "")),
        captured_at=str(
            meta.get("captured_at") or meta.get("created") or bullets.get("captured", "")
        ),
        published_at=str(meta.get("published") or meta.get("published_at") or ""),
        meta=meta,
    )
