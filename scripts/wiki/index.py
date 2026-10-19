"""index.md and log.md maintenance. The log is append-only."""

from __future__ import annotations

import re
from pathlib import Path


def add_index_entry(index_path: Path, section: str, link: str, note: str) -> bool:
    """Add `- [[link]] - note` under `## section`. Returns False if already listed."""
    text = index_path.read_text(encoding="utf-8")
    if f"[[{link}]]" in text:
        return False
    heading = re.search(rf"^## {re.escape(section)}[ \t]*$", text, re.MULTILINE)
    if not heading:
        raise ValueError(f"index.md has no '## {section}' section")
    end = heading.end()
    next_heading = re.search(r"^## ", text[end:], re.MULTILINE)
    stop = end + next_heading.start() if next_heading else len(text)
    block = text[end:stop].rstrip("\n")
    entry = f"- [[{link}]] - {note}" if note else f"- [[{link}]]"
    new_block = f"{block}\n{entry}\n\n" if block.strip() else f"\n\n{entry}\n\n"
    index_path.write_text(text[:end] + new_block + text[stop:], encoding="utf-8")
    return True


def set_health(index_path: Path, key: str, value: str) -> None:
    text = index_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^- {re.escape(key)}:.*$", re.MULTILINE)
    if not pattern.search(text):
        raise ValueError(f"index.md has no health line '{key}'")
    index_path.write_text(pattern.sub(f"- {key}: {value}", text, count=1), encoding="utf-8")


def append_log(log_path: Path, heading: str, fields: dict[str, str]) -> None:
    """Append one entry. Never rewrites existing content."""
    lines = [f"\n## {heading}", ""]
    lines += [f"- {key}: {value}" for key, value in fields.items()]
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
