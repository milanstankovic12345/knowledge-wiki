"""Command line entry point: `python -m scripts.app ingest <path under raw/>`."""

from __future__ import annotations

import argparse
import sys

from scripts.config import load_vault
from scripts.extractors.tools import ExtractionError
from scripts.extractors.youtube import capture_youtube
from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.security import PathRejected, UrlRejected
from scripts.wiki.ingest import IngestError, ingest_file


def _batch(vault, args) -> int:
    from scripts.batch import (
        YOUTUBE_PAUSE,
        collect_items,
        label,
        run_items,
        summary,
        url_list_path,
        write_failed_list,
    )

    items = collect_items(vault, args.targets, args.recursive)
    if args.dry_run:
        for item in items:
            print(label(item))
        print(f"{len(items)} item(s) would be processed.")
        return 0
    outcomes = run_items(vault, items, pause=YOUTUBE_PAUSE)
    print(f"Done: {summary(outcomes)}.")
    if len(args.targets) == 1 and (lst := url_list_path(vault, args.targets[0])):
        if failed := write_failed_list(lst, outcomes):
            print(f"Failed URLs saved to {failed.name}; fix them and rerun.")
    return 0 if all(o.ok for o in outcomes) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.app")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser(
        "ingest", help="ingest one Markdown/text/PDF/audio/video file from raw/"
    )
    ingest.add_argument("path")
    youtube = sub.add_parser("youtube", help="capture a YouTube video's subtitles and ingest them")
    youtube.add_argument("url")
    batch = sub.add_parser(
        "batch", help="ingest many sources: a text file of URLs, a folder under raw/, or paths/URLs"
    )
    batch.add_argument("targets", nargs="+")
    batch.add_argument("--recursive", action="store_true", help="include subfolders of a folder")
    batch.add_argument("--dry-run", action="store_true", help="list what would be ingested")
    watch = sub.add_parser(
        "watch", help="ingest new raw/articles clips and inbox/pending URL lists as they appear"
    )
    watch.add_argument("--interval", type=float, default=30.0, help="seconds between scans")
    watch.add_argument(
        "--folders", nargs="+", default=["articles"], help="raw/ subfolders to watch"
    )
    sub.add_parser("bot", help="run the Telegram bot (long polling)")
    sub.add_parser("lint", help="check the wiki for broken links, orphans and missing sources")
    args = parser.parse_args(argv)

    vault = load_vault()
    if args.command == "bot":
        from scripts.telegram.bot import BotConfigError, run_bot

        try:
            run_bot(vault)
        except BotConfigError as exc:
            print(f"Cannot start: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.command == "batch":
        return _batch(vault, args)
    if args.command == "watch":
        from scripts.batch import watch as run_watch

        try:
            run_watch(vault, args.interval, tuple(args.folders))
        except KeyboardInterrupt:
            print("Stopped.")
        return 0
    if args.command == "lint":
        from scripts.wiki.lint import format_report, run_lint

        report = run_lint(vault)
        print(format_report(report))
        return 1 if report.findings else 0
    try:
        if args.command == "youtube":
            path, meta = capture_youtube(args.url, vault)
            print(f"Captured: {meta.title} ({meta.channel}, {meta.transcript_kind} subtitles)")
            result = ingest_file(vault, path)
        else:
            result = ingest_file(vault, args.path)
    except (PathRejected, UrlRejected) as exc:
        print(f"Rejected: {exc}", file=sys.stderr)
        return 2
    except CloudBlocked as exc:
        print(f"Blocked: {exc}", file=sys.stderr)
        return 3
    except (ProviderUnavailable, IngestError, ExtractionError) as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    if result.status == "duplicate":
        print(f"Already ingested. Source summary: {result.summary_path}")
        return 0
    print(f"Ingested. Source summary: {result.summary_path}")
    if result.book_path:
        print(f"Book page: {result.book_path}")
    for note in result.needs_review:
        print(f"Needs review: {note}")
    print(f"Topics created: {', '.join(result.created) or '-'}")
    print(f"Topics updated: {', '.join(result.updated) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
