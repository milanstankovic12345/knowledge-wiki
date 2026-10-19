"""Command line entry point: `python -m scripts.app ingest <path under raw/>`."""

from __future__ import annotations

import argparse
import sys

from scripts.config import load_vault
from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.security import PathRejected
from scripts.wiki.ingest import IngestError, ingest_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.app")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="ingest one Markdown/text file from raw/")
    ingest.add_argument("path")
    args = parser.parse_args(argv)

    vault = load_vault()
    try:
        result = ingest_file(vault, args.path)
    except PathRejected as exc:
        print(f"Rejected: {exc}", file=sys.stderr)
        return 2
    except CloudBlocked as exc:
        print(f"Blocked: {exc}", file=sys.stderr)
        return 3
    except (ProviderUnavailable, IngestError) as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    if result.status == "duplicate":
        print(f"Already ingested. Source summary: {result.summary_path}")
        return 0
    print(f"Ingested. Source summary: {result.summary_path}")
    print(f"Topics created: {', '.join(result.created) or '-'}")
    print(f"Topics updated: {', '.join(result.updated) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
