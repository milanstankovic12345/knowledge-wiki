"""Shared helpers for extractors that shell out to ffmpeg/ffprobe."""

from __future__ import annotations

import shutil
import subprocess


class ExtractionError(RuntimeError):
    """A deterministic extraction step failed. Messages never include source content."""


def fmt_time(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def run_tool(args: list[str]) -> str:
    """Run an external tool without a shell and return stdout.

    stderr is dropped from errors: tools can echo file names or media text.
    """
    exe = shutil.which(args[0])
    if exe is None:
        raise ExtractionError(f"{args[0]} is not installed or not on PATH")
    try:
        done = subprocess.run(  # noqa: S603 - fixed argv, no shell, validated paths
            [exe, *args[1:]], check=True, capture_output=True, text=True, stdin=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as exc:
        raise ExtractionError(f"{args[0]} failed with exit code {exc.returncode}") from exc
    return done.stdout
