"""Capture a YouTube video's subtitles with yt-dlp as a raw Markdown transcript with timestamps."""

from __future__ import annotations

import json
import re
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from scripts.config import Vault
from scripts.extractors import tools
from scripts.extractors.audio import MARKER_EVERY, TIME_MARKER
from scripts.extractors.tools import ExtractionError, RateLimited, fmt_time
from scripts.security import UrlRejected
from scripts.storage import dump_frontmatter, parse_frontmatter, slugify

Runner = Callable[..., str]

HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
LANG_KEY = re.compile(r"[A-Za-z0-9-]{1,20}")  # subtitle keys from yt-dlp, safe to pass on
URL_IN_TEXT = re.compile(r"https?://[^\s<>\"')]+")
ID_PATH_PREFIXES = ("/shorts/", "/embed/", "/live/")
YT_DLP_TIMEOUT = 120.0
RATE_LIMIT_WAITS = (20.0, 60.0)  # seconds to wait before each retry after an HTTP 429
MAX_SUBTITLE_BYTES = 20 * 1024 * 1024
DEFAULT_LANGS = ["en.*"]


@dataclass
class YoutubeMeta:
    video_id: str
    title: str
    channel: str
    duration_seconds: int
    language: str
    transcript_kind: str  # "manual" | "auto"


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def find_youtube_url(text: str) -> str:
    """First YouTube-host URL in `text`, or "". Whether its form is supported is decided later."""
    return next((u for u in URL_IN_TEXT.findall(text) if _host(u) in HOSTS), "")


def parse_youtube_url(url: str) -> str:
    """Return the video id of a single-video YouTube URL, or raise UrlRejected."""
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError as exc:
        raise UrlRejected("not a valid YouTube video URL") from exc
    if parts.scheme not in ("http", "https") or parts.username or parts.password or port:
        raise UrlRejected("not a valid YouTube video URL")
    host = (parts.hostname or "").lower()
    if host not in HOSTS:
        raise UrlRejected("only youtube.com and youtu.be video links are supported")
    if host == "youtu.be":
        candidate = parts.path.strip("/")
    elif parts.path == "/watch":
        values = parse_qs(parts.query).get("v", [])
        candidate = values[0] if len(values) == 1 else ""
    elif parts.path.startswith(ID_PATH_PREFIXES):
        candidate = parts.path.split("/")[2] if parts.path.count("/") == 2 else ""
    else:
        candidate = ""
    if not VIDEO_ID.fullmatch(candidate):
        raise UrlRejected("that YouTube link is not a single video (playlists are not supported)")
    return candidate


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _yt_dlp(
    runner: Runner,
    args: list[str],
    video_id: str,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    argv = ["yt-dlp", "--skip-download", "--no-playlist", "--no-warnings", *args]
    for wait in (*RATE_LIMIT_WAITS, None):
        try:
            runner([*argv, "--", canonical_url(video_id)], timeout=YT_DLP_TIMEOUT)
            return
        except RateLimited as exc:
            if wait is None:
                raise ExtractionError(
                    "YouTube is rate-limiting subtitle downloads for this video right now "
                    "(HTTP 429). Wait a few minutes and send it again."
                ) from exc
            sleep(wait)
        except ExtractionError as exc:
            text = str(exc)
            if "not installed" in text or "timed out" in text:
                raise
            # stderr is dropped on purpose; the usual causes are the ones below.
            raise ExtractionError(
                "yt-dlp could not fetch this video (private, age-restricted, removed, "
                "or yt-dlp needs updating)"
            ) from exc


def _matching(keys: list[str], patterns: list[str]) -> list[str]:
    """Subtitle keys in `patterns` order; per pattern the shortest key first."""
    found: list[str] = []
    for pattern in patterns:
        try:
            rx = re.compile(pattern)
        except re.error:
            continue
        for key in sorted(keys, key=lambda k: (len(k), k)):
            if rx.fullmatch(key) and key not in found and LANG_KEY.fullmatch(key):
                found.append(key)
    return found


def pick_subtitles(info: dict[str, Any], patterns: list[str]) -> tuple[str, str]:
    """(language key, "manual" | "auto"). Manual subtitles beat auto-generated ones."""
    for kind, field in (("manual", "subtitles"), ("auto", "automatic_captions")):
        tracks = info.get(field) or {}
        keys = [k for k, v in tracks.items() if v]
        chosen = _matching(keys, patterns)
        if chosen:
            return chosen[0], kind
    raise ExtractionError("this video has no subtitles in the configured languages")


def cues_from_json3(data: dict[str, Any]) -> list[tuple[float, str]]:
    """(start seconds, text) per non-empty cue; consecutive repeated lines are dropped."""
    cues: list[tuple[float, str]] = []
    for event in data.get("events") or []:
        segs = event.get("segs")
        if not segs:
            continue
        text = " ".join("".join(str(s.get("utf8", "")) for s in segs).split())
        if not text or (cues and cues[-1][1] == text):
            continue
        cues.append((float(event.get("tStartMs", 0)) / 1000.0, text))
    return cues


def transcript_markdown(cues: list[tuple[float, str]]) -> str:
    """Paragraph per ~30 s window, each introduced by a time marker the ingest prompt can cite."""
    blocks: list[str] = []
    last_marker = -MARKER_EVERY
    words: list[str] = []
    for start, text in cues:
        if start - last_marker >= MARKER_EVERY:
            if words:
                blocks.append(" ".join(words))
                words = []
            blocks.append(TIME_MARKER.format(t=fmt_time(start)))
            last_marker = start
        words.append(text)
    if words:
        blocks.append(" ".join(words))
    return "\n\n".join(blocks)


def _read_json(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_SUBTITLE_BYTES:
        raise ExtractionError("subtitle file is too large")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ExtractionError("could not read the downloaded subtitles") from exc
    if not isinstance(data, dict):
        raise ExtractionError("could not read the downloaded subtitles")
    return data


def _existing(raw_dir: Path, video_id: str) -> tuple[Path, YoutubeMeta] | None:
    for path in sorted(raw_dir.glob(f"*-{video_id}.md")):
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("video_id") == video_id:
            return path, YoutubeMeta(
                video_id,
                str(meta.get("title", "")),
                str(meta.get("author", "")),
                int(meta.get("duration_seconds") or 0),
                str(meta.get("language", "")),
                str(meta.get("transcript_kind", "")),
            )
    return None


def capture_youtube(
    url: str,
    vault: Vault,
    runner: Runner | None = None,
    privacy: str = "",
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[Path, YoutubeMeta]:
    """Fetch subtitles for `url` into `raw/youtube/<title>-<id>.md`. Existing captures are kept."""
    video_id = parse_youtube_url(url)
    raw_dir = vault.path("raw") / "youtube"
    if (known := _existing(raw_dir, video_id)) is not None:
        return known

    runner = runner or tools.run_tool  # resolved at call time so tests can patch it
    settings = vault.settings.get("youtube", {})
    patterns = [str(p) for p in settings.get("subtitle_langs") or DEFAULT_LANGS]

    with tempfile.TemporaryDirectory(prefix="yt-") as tmp:
        out = str(Path(tmp) / "%(id)s")
        _yt_dlp(runner, ["--write-info-json", "-o", out], video_id, sleep)
        info = _read_json(Path(tmp) / f"{video_id}.info.json")
        lang, kind = pick_subtitles(info, patterns)
        flag = "--write-subs" if kind == "manual" else "--write-auto-subs"
        _yt_dlp(
            runner,
            [flag, "--sub-langs", lang, "--sub-format", "json3", "-o", out],
            video_id,
            sleep,
        )
        subtitle = Path(tmp) / f"{video_id}.{lang}.json3"
        if not subtitle.is_file():
            raise ExtractionError("yt-dlp did not return subtitles for this video")
        cues = cues_from_json3(_read_json(subtitle))

    if not cues:
        raise ExtractionError("the subtitles for this video are empty")
    title = str(info.get("title") or "").strip() or video_id
    channel = str(info.get("channel") or info.get("uploader") or "").strip()
    upload = str(info.get("upload_date") or "")
    meta = YoutubeMeta(video_id, title, channel, int(info.get("duration") or 0), lang, kind)

    out_path = raw_dir / f"{slugify(title)}-{video_id}.md"
    if not out_path.exists():
        raw_dir.mkdir(parents=True, exist_ok=True)
        front: dict[str, Any] = {
            "title": title,
            "source_type": "youtube",
            "source_url": canonical_url(video_id),
            "author": channel,
            "video_id": video_id,
            "upload_date": f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) == 8 else "",
            "duration_seconds": meta.duration_seconds,
            "language": lang,
            "transcript_kind": kind,
            "captured_at": date.today().isoformat(),
        }
        if privacy:
            front["privacy"] = privacy
        out_path.write_text(dump_frontmatter(front, transcript_markdown(cues) + "\n"), "utf-8")
    return out_path, meta
