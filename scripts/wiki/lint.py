"""Wiki health check. Pure file scanning, no model: it reports problems and never edits pages."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from scripts.config import Vault
from scripts.storage import parse_frontmatter
from scripts.wiki.index import append_log, set_health

NO_CONTENT = re.compile(
    r"[-*\s]*(none|n/a|no contradictions?)( recorded| noted| found)?\.?\s*", re.I
)
LINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
SOURCE_FIELDS = (
    "source_type",
    "raw_path",
    "captured_at",
    "content_hash",
    "privacy",
    "llm_model",
    "processed_at",
)
DESCRIPTIONS = {
    "broken-link": "link to a page that does not exist",
    "stale-index": "index.md entry whose page does not exist",
    "not-indexed": "page missing from index.md",
    "orphan": "not in index.md and no other page links here",
    "no-source": "no source summary behind this page",
    "missing-provenance": "source summary missing required provenance fields",
    "open-contradiction": "has an unresolved Contradictions section",
}


@dataclass
class Finding:
    kind: str
    page: str
    detail: str = ""


@dataclass
class LintReport:
    pages: int = 0
    findings: list[Finding] = field(default_factory=list)


def link_targets(text: str) -> list[str]:
    return [m.group(1).strip().removesuffix(".md") for m in LINK.finditer(text)]


_targets = link_targets


def _section(body: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return match.group(1).strip() if match else ""


def lint(vault: Vault) -> LintReport:
    wiki = vault.root / "wiki"
    pages = {p.relative_to(wiki).with_suffix("").as_posix(): p for p in sorted(wiki.rglob("*.md"))}
    stems: dict[str, int] = defaultdict(int)
    for name in pages:
        stems[Path(name).name] += 1

    def exists(target: str) -> bool:
        return target in pages or (Path(target).name == target and stems[target] > 0)

    def resolve(target: str) -> str | None:
        if target in pages:
            return target
        return next((n for n in pages if Path(n).name == target), None)

    index_path = vault.root / "index.md"
    index_text = index_path.read_text("utf-8") if index_path.exists() else ""
    indexed = {hit for t in _targets(index_text) if (hit := resolve(t))}
    inbound: dict[str, set[str]] = defaultdict(set)
    report = LintReport(pages=len(pages))
    add = report.findings.append

    for target in _targets(index_text):
        if not exists(target):
            add(Finding("stale-index", "index.md", f"[[{target}]]"))
    for name, path in pages.items():
        meta, body = parse_frontmatter(path.read_text("utf-8"))
        rel = f"wiki/{name}.md"
        for target in dict.fromkeys(_targets(body)):
            hit = resolve(target)
            if hit is None:
                add(Finding("broken-link", rel, f"[[{target}]]"))
            elif hit != name:
                inbound[hit].add(name)
        kind = str(meta.get("type", ""))
        if kind == "source-summary":
            missing = [f for f in SOURCE_FIELDS if not meta.get(f)]
            if missing:
                add(Finding("missing-provenance", rel, ", ".join(missing)))
        elif kind in {"topic", "concept", "book", "person", "organization"}:
            listed = meta.get("sources") or []
            if not listed and not any(t.startswith("sources/") for t in _targets(body)):
                add(Finding("no-source", rel))
        contradictions = _section(body, "Contradictions")
        if contradictions and not NO_CONTENT.fullmatch(contradictions):
            add(Finding("open-contradiction", rel))
    # Ingest catalogues the book/video page, not its source summary, so a summary counts as
    # indexed when an indexed page links to it (one hop).
    reachable = {n for n in pages if n.startswith("sources/") and inbound[n] & indexed}
    for name in pages:
        if name in indexed or name in reachable:
            continue
        # Linked from somewhere but not catalogued, or reachable from nowhere at all.
        add(Finding("not-indexed" if inbound[name] else "orphan", f"wiki/{name}.md"))
    report.findings.sort(key=lambda f: (f.kind, f.page, f.detail))
    return report


def format_report(report: LintReport, per_kind: int = 8) -> str:
    if not report.findings:
        return f"Wiki is healthy: {report.pages} pages checked, no issues."
    groups: dict[str, list[Finding]] = defaultdict(list)
    for f in report.findings:
        groups[f.kind].append(f)
    lines = [f"{len(report.findings)} issue(s) in {report.pages} pages."]
    for kind, items in groups.items():
        lines.append(f"\n{kind} ({len(items)}): {DESCRIPTIONS.get(kind, '')}")
        for f in items[:per_kind]:
            lines.append(f"- {f.page}" + (f"  {f.detail}" if f.detail else ""))
        if len(items) > per_kind:
            lines.append(f"- ... and {len(items) - per_kind} more")
    return "\n".join(lines)


def run_lint(vault: Vault) -> LintReport:
    """Lint, then record the result in index.md's health section and the append-only log."""
    report = lint(vault)
    now = datetime.now().astimezone()
    counts: dict[str, int] = defaultdict(int)
    for f in report.findings:
        counts[f.kind] += 1
    index_path = vault.root / "index.md"
    if index_path.exists():
        stamp = now.isoformat(timespec="seconds")
        set_health(index_path, "Last lint", f"{stamp} ({len(report.findings)} issues)")
    log_path = vault.root / "log.md"
    if log_path.exists():
        append_log(
            log_path,
            f"[{now.strftime('%Y-%m-%d %H:%M')}] lint | {report.pages} pages",
            {
                "Issues": str(len(report.findings)),
                "By kind": ", ".join(f"{k}: {n}" for k, n in sorted(counts.items())) or "none",
            },
        )
    return report
