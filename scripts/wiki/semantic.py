"""Cached page embeddings and cosine scoring for hybrid search. Local embedder only."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Protocol

from sqlalchemy import select

from scripts.config import Vault
from scripts.database import PageEmbedding, open_db
from scripts.storage import parse_frontmatter

EMBED_CHARS = 2000


class Embedder(Protocol):
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _page_text(raw: str, stem: str) -> str:
    meta, body = parse_frontmatter(raw)
    return f"{meta.get('title') or stem}\n{body.strip()[:EMBED_CHARS]}"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def sync_embeddings(vault: Vault, embedder: Embedder) -> dict[str, list[float]]:
    """Embed new or changed wiki pages, drop removed ones, and return path -> vector.

    Raises ProviderUnavailable if the embedder is down; callers fall back to keyword search.
    """
    pages = {
        p.relative_to(vault.root).as_posix(): _page_text(p.read_text(encoding="utf-8"), p.stem)
        for p in sorted((vault.root / "wiki").rglob("*.md"))
    }
    db = open_db(vault.path("database"))
    try:
        rows = {r.path: r for r in db.scalars(select(PageEmbedding))}
        for path in set(rows) - set(pages):
            db.delete(rows[path])
        stale = []
        for path, text in pages.items():
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            row = rows.get(path)
            if row is None or row.content_hash != digest or row.model != embedder.model:
                stale.append((path, digest, text))
        if stale:
            vectors = embedder.embed([t for _, _, t in stale])
            for (path, digest, _), vector in zip(stale, vectors, strict=True):
                row = rows.get(path) or PageEmbedding(path=path)
                row.content_hash, row.model, row.vector = digest, embedder.model, json.dumps(vector)
                db.add(row)
        db.commit()
        return {
            r.path: json.loads(r.vector)
            for r in db.scalars(select(PageEmbedding))
            if r.path in pages
        }
    finally:
        db.close()


def semantic_scores(vault: Vault, embedder: Embedder, query: str) -> dict[str, float]:
    vectors = sync_embeddings(vault, embedder)
    q = embedder.embed([query])[0]
    return {path: cosine(q, vec) for path, vec in vectors.items()}
