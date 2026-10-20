"""Suggest missing links between related topic and concept pages, and apply one on approval.

Suggestions come from cached page embeddings (no LLM). Nothing is written until `apply_link`
is called for a specific pair, which the Telegram `/link` flow only does after a button press.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from scripts.config import Vault
from scripts.storage import parse_frontmatter
from scripts.wiki.index import append_log
from scripts.wiki.integrate import append_to_section
from scripts.wiki.lint import link_targets
from scripts.wiki.semantic import Embedder, cosine, sync_embeddings

LINKABLE = ("topics/", "concepts/")
SECTION = "Related topics"
DEFAULT_MIN_SIMILARITY = 0.75


@dataclass(frozen=True)
class Suggestion:
    a: str  # wiki-relative page name without suffix, e.g. "topics/agentic-rag"
    b: str
    similarity: float


def _name(path: str) -> str:
    return path.removeprefix("wiki/").removesuffix(".md")


def _linkable(name: str) -> bool:
    return name.startswith(LINKABLE)


def suggest_links(vault: Vault, embedder: Embedder, limit: int = 5) -> list[Suggestion]:
    """Most similar unlinked topic/concept pairs, best first. Raises ProviderUnavailable."""
    vectors = {
        _name(path): vec
        for path, vec in sync_embeddings(vault, embedder).items()
        if _linkable(_name(path))
    }
    wiki = vault.root / "wiki"
    stems: dict[str, str] = {}
    for name in vectors:
        stems.setdefault(Path(name).name, name)
    linked: set[frozenset[str]] = set()
    for name in vectors:
        _, body = parse_frontmatter((wiki / f"{name}.md").read_text(encoding="utf-8"))
        for target in link_targets(body):
            hit = target if target in vectors else stems.get(target)
            if hit and hit != name:
                linked.add(frozenset((name, hit)))  # either direction counts as linked
    threshold = float(vault.settings.get("link", {}).get("min_similarity", DEFAULT_MIN_SIMILARITY))
    names = sorted(vectors)
    found = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if frozenset((a, b)) in linked:
                continue
            similarity = cosine(vectors[a], vectors[b])
            if similarity >= threshold:
                found.append(Suggestion(a, b, round(similarity, 3)))
    found.sort(key=lambda s: (-s.similarity, s.a, s.b))
    return found[:limit]


def _page(vault: Vault, name: str) -> Path:
    wiki = (vault.root / "wiki").resolve()
    path = (wiki / f"{name}.md").resolve()
    if not path.is_relative_to(wiki) or not path.is_file():
        raise ValueError(f"not a wiki page: {name}")
    return path


def _add_link(path: Path, target: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if target in link_targets(text):
        return False
    path.write_text(append_to_section(text, SECTION, f"- [[{target}]]"), encoding="utf-8")
    return True


def apply_link(vault: Vault, a: str, b: str) -> bool:
    """Link two pages to each other under '## Related topics'. True if anything changed."""
    page_a, page_b = _page(vault, a), _page(vault, b)
    changed = [_add_link(page_a, b), _add_link(page_b, a)]
    if not any(changed):
        return False
    log_path = vault.root / "log.md"
    if log_path.exists():
        now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        append_log(log_path, f"[{now}] link | {a} <-> {b}", {"Approved": "via /link"})
    return True
