"""Ingest many sources in one go (`batch`) or pick up new ones as they appear (`watch`).

Both are thin loops over the single-source pipeline: ingest is idempotent (duplicates are cheap),
so re-running either is always safe. Items run one at a time because the GPU is shared with Ollama.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.config import Vault
from scripts.extractors.tools import ExtractionError
from scripts.extractors.url import capture_article
from scripts.extractors.youtube import capture_youtube, find_youtube_url
from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.security import PathRejected, UrlRejected, redact_secrets
from scripts.wiki.ingest import URL_IN_TEXT, IngestError, ingest_file

SETTLE_SECONDS = 5.0  # a file touched more recently than this may still be being written
LABEL_MAX = 100
YOUTUBE_PAUSE = 8.0  # seconds between consecutive videos; YouTube rate-limits subtitle fetches
SIDECAR_SUFFIXES = (".caption.txt",)

Report = Callable[[str], None]


@dataclass
class Outcome:
    item: str
    status: str  # "ingested" | "duplicate" | "failed" | "rejected" | "unavailable"
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("ingested", "duplicate")


def label(item: str) -> str:
    return item if len(item) <= LABEL_MAX else item[: LABEL_MAX - 1] + "…"


def ingest_item(
    vault: Vault,
    item: str,
    capture_yt: Callable[..., Any] = capture_youtube,
    capture_art: Callable[..., Path] = capture_article,
    ingest: Callable[..., Any] = ingest_file,
) -> Outcome:
    """Ingest one URL or raw/ path. Never raises: every failure becomes an Outcome."""
    try:
        if item.lower().startswith(("http://", "https://")):
            if find_youtube_url(item):
                path = capture_yt(item, vault)[0]
            else:
                path = capture_art(item, vault)
        else:
            path = item
        result = ingest(vault, path)
    except (PathRejected, UrlRejected) as exc:
        return Outcome(item, "rejected", redact_secrets(str(exc)))
    except ProviderUnavailable as exc:
        return Outcome(item, "unavailable", redact_secrets(str(exc)))
    except (CloudBlocked, IngestError, ExtractionError, OSError) as exc:
        return Outcome(item, "failed", redact_secrets(str(exc)))
    except Exception as exc:  # noqa: BLE001 - one bad item must not stop a long run
        return Outcome(item, "failed", f"unexpected error ({type(exc).__name__})")
    return Outcome(item, "duplicate" if result.status == "duplicate" else "ingested")


def parse_url_list(text: str) -> list[str]:
    """URLs from a list file: one per line, `#` comments and blank lines ignored, order kept."""
    seen: dict[str, None] = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            for url in URL_IN_TEXT.findall(line):
                seen.setdefault(url, None)
    return list(seen)


def _allowed_ext(vault: Vault) -> set[str]:
    exts = vault.settings["allowed_extensions"]
    return {e for kind in ("document", "audio", "video", "image") for e in exts[kind]}


def sources_in(vault: Vault, folder: Path, recursive: bool = False) -> list[Path]:
    allowed = _allowed_ext(vault)
    found = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(
        p
        for p in found
        if p.is_file()
        and p.suffix.lower() in allowed
        and not p.name.lower().endswith(SIDECAR_SUFFIXES)
    )


def _under_raw(vault: Vault, path: Path) -> bool:
    return path.resolve().is_relative_to((vault.root / "raw").resolve())


def url_list_path(vault: Vault, target: str) -> Path | None:
    """The target as a URL-list file (a real file outside raw/), else None."""
    if target.lower().startswith(("http://", "https://")):
        return None
    path = Path(target)
    if not path.is_absolute():
        path = vault.root / path
    return path if path.is_file() and not _under_raw(vault, path) else None


def collect_items(vault: Vault, targets: list[str], recursive: bool = False) -> list[str]:
    """Expand batch targets into items. A file outside raw/ is a URL list; inside raw/ a source."""
    items: dict[str, None] = {}
    for target in targets:
        if target.lower().startswith(("http://", "https://")):
            items.setdefault(target, None)
            continue
        path = Path(target)
        if not path.is_absolute():
            path = vault.root / path
        if path.is_dir():
            for source in sources_in(vault, path, recursive):
                items.setdefault(str(source), None)
        elif url_list_path(vault, target):
            for url in parse_url_list(path.read_text(encoding="utf-8", errors="replace")):
                items.setdefault(url, None)
        else:
            items.setdefault(str(path), None)
    return list(items)


def run_items(
    vault: Vault,
    items: list[str],
    report: Report = print,
    ingest: Callable[[Vault, str], Outcome] = ingest_item,
    stop_when_unavailable: bool = False,
    pause: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Outcome]:
    outcomes: list[Outcome] = []
    for n, item in enumerate(items, 1):
        if pause and n > 1 and find_youtube_url(item) and find_youtube_url(items[n - 2]):
            sleep(pause)
        outcome = ingest(vault, item)
        outcomes.append(outcome)
        tail = f" - {outcome.detail}" if outcome.detail else ""
        report(f"[{n}/{len(items)}] {outcome.status}: {label(item)}{tail}")
        if stop_when_unavailable and outcome.status == "unavailable":
            break
    return outcomes


def summary(outcomes: list[Outcome]) -> str:
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    return ", ".join(f"{n} {s}" for s, n in sorted(counts.items())) or "nothing to do"


def write_failed_list(list_path: Path, outcomes: list[Outcome]) -> Path | None:
    """Keep the failed URLs next to the list so they can be fixed and rerun."""
    failed = [o.item for o in outcomes if not o.ok and o.item.lower().startswith("http")]
    if not failed:
        return None
    out = list_path.with_name(list_path.name + ".failed.txt")
    out.write_text("\n".join(failed) + "\n", encoding="utf-8")
    return out


# --- watch --------------------------------------------------------------------------------------


def _fresh(path: Path, now: float, settle: float) -> bool:
    return now - path.stat().st_mtime < settle


def _move_unique(path: Path, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target, n = folder / path.name, 1
    while target.exists():
        n += 1
        target = folder / f"{path.stem}-{n}{path.suffix}"
    path.replace(target)
    return target


def run_cycle(
    vault: Vault,
    attempted: dict[str, float],
    folders: tuple[str, ...] = ("articles",),
    now: float | None = None,
    settle: float = SETTLE_SECONDS,
    report: Report = print,
    ingest: Callable[[Vault, str], Outcome] = ingest_item,
    pause: float = 0.0,
) -> list[Outcome]:
    """One scan: URL lists in inbox/pending, then new files in the watched raw/ folders.

    `attempted` maps a file to the mtime we last processed, so a broken file is retried only
    after it changes (or after a restart), never in a tight loop.
    """
    now = time.time() if now is None else now
    inbox = vault.path("inbox")
    done: list[Outcome] = []

    pending = inbox / "pending"
    for lst in sorted(pending.glob("*.txt")) if pending.is_dir() else []:
        if _fresh(lst, now, settle):
            continue
        report(f"inbox list: {lst.name}")
        urls = parse_url_list(lst.read_text(encoding="utf-8", errors="replace"))
        outcomes = run_items(vault, urls, report, ingest, stop_when_unavailable=True, pause=pause)
        done += outcomes
        if any(o.status == "unavailable" for o in outcomes):
            return done  # leave the list where it is; the next cycle retries it
        failed = [o.item for o in outcomes if not o.ok]
        if failed:
            lst.write_text("\n".join(failed) + "\n", encoding="utf-8")
            _move_unique(lst, inbox / "failed")
        else:
            _move_unique(lst, inbox / "processed")

    for name in folders:
        folder = vault.path("raw") / name
        for path in sources_in(vault, folder) if folder.is_dir() else []:
            if _fresh(path, now, settle):
                continue
            mtime = path.stat().st_mtime
            if attempted.get(str(path)) == mtime:
                continue
            outcome = run_items(vault, [str(path)], report, ingest)[0]
            done.append(outcome)
            if outcome.status == "unavailable":
                return done
            attempted[str(path)] = mtime
    return done


def watch(
    vault: Vault,
    interval: float = 30.0,
    folders: tuple[str, ...] = ("articles",),
    report: Report = print,
    sleep: Callable[[float], None] = time.sleep,
    max_cycles: int | None = None,
) -> None:
    """Poll until interrupted (Ctrl+C is handled by the caller)."""
    attempted: dict[str, float] = {}
    report(
        f"Watching raw/{', raw/'.join(folders)} and inbox/pending every {interval:g}s "
        "(Ctrl+C stops)."
    )
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        run_cycle(vault, attempted, folders, report=report, pause=YOUTUBE_PAUSE)
        cycles += 1
        if max_cycles is None or cycles < max_cycles:
            sleep(interval)
