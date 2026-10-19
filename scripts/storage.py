"""Hashing, slugs and Markdown front matter helpers."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "untitled"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FM.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(meta, dict):
        return {}, text
    return meta, text[match.end() :]


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{head}\n---\n\n{body.lstrip()}"
