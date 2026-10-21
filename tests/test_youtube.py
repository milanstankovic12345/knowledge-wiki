import json
from pathlib import Path

import pytest

from scripts.extractors import youtube as yt
from scripts.extractors.tools import ExtractionError, RateLimited
from scripts.security import UrlRejected
from scripts.storage import parse_frontmatter
from scripts.wiki.ingest import ingest_file

VID = "dQw4w9WgXcQ"


def json3(*cues):
    """cues: (start seconds, text) pairs in yt-dlp's json3 shape."""
    return {
        "wireMagic": "pb3",
        "events": [{"tStartMs": int(s * 1000), "segs": [{"utf8": t}]} for s, t in cues],
    }


def info(manual=(), auto=("en",), title="Intro to Obsidian", **extra):
    track = [{"ext": "json3", "url": "https://example.invalid/x"}]
    return {
        "id": VID,
        "title": title,
        "channel": "Some Channel",
        "upload_date": "20240131",
        "duration": 754,
        "subtitles": {k: track for k in manual},
        "automatic_captions": {k: track for k in auto},
        **extra,
    }


class FakeYtDlp:
    """Stands in for run_tool: writes what yt-dlp would write into the -o directory."""

    def __init__(self, info_json, subs=None):
        self.info_json, self.subs = info_json, subs or {}
        self.calls: list[tuple[list[str], float | None]] = []

    def __call__(self, args, timeout=None):
        self.calls.append((args, timeout))
        folder = Path(args[args.index("-o") + 1]).parent
        if "--write-info-json" in args:
            (folder / f"{VID}.info.json").write_text(json.dumps(self.info_json), "utf-8")
        if "--sub-langs" in args:
            lang = args[args.index("--sub-langs") + 1]
            if lang in self.subs:
                (folder / f"{VID}.{lang}.json3").write_text(json.dumps(self.subs[lang]), "utf-8")
        return ""


CUES = json3((1.0, "Hello and welcome."), (12.0, "Today we set up"), (40.0, "a vault."))
URL = f"https://youtu.be/{VID}"


# --- URL parsing --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"https://youtube.com/watch?v={VID}&t=30s",
        f"https://m.youtube.com/watch?v={VID}",
        f"https://youtu.be/{VID}?si=abc",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/embed/{VID}",
        f"https://www.youtube.com/watch?v={VID}&list=PL123",  # the single video wins
    ],
)
def test_valid_urls_give_the_video_id(url):
    assert yt.parse_youtube_url(url) == VID


@pytest.mark.parametrize(
    "url",
    [
        f"https://evil.com/watch?v={VID}",
        f"https://youtube.com.evil.com/watch?v={VID}",
        f"https://www.youtube.com@evil.com/watch?v={VID}",
        f"https://user:pw@www.youtube.com/watch?v={VID}",
        f"ftp://www.youtube.com/watch?v={VID}",
        "https://www.youtube.com/playlist?list=PL123",
        "https://www.youtube.com/watch?v=short",
        f"https://www.youtube.com/watch?v={VID};rm -rf /",
        f"https://www.youtube.com/watch?v={VID}&v={VID}",
        "https://www.youtube.com/",
        "https://youtu.be/",
    ],
)
def test_other_urls_are_rejected(url):
    with pytest.raises(UrlRejected):
        yt.parse_youtube_url(url)


def test_find_youtube_url_in_a_sentence():
    text = f"see https://example.com/a and {URL} please"
    assert yt.find_youtube_url(text) == URL
    assert yt.find_youtube_url("https://example.com/a") == ""


# --- subtitle choice ----------------------------------------------------------------------------


def test_manual_subtitles_beat_auto_generated():
    chosen = yt.pick_subtitles(info(manual=["sl"], auto=["en"]), ["en.*", "sl.*"])
    assert chosen == ("sl", "manual")


def test_language_order_follows_settings_and_prefers_the_original_key():
    meta = info(manual=["sr-Latn", "sl", "en-GB"])
    assert yt.pick_subtitles(meta, ["sl.*", "en.*"]) == ("sl", "manual")
    assert yt.pick_subtitles(meta, ["en.*", "sl.*"]) == ("en-GB", "manual")


def test_auto_subtitles_are_used_when_no_manual_ones_match():
    assert yt.pick_subtitles(info(manual=["de"], auto=["en"]), ["en.*"]) == ("en", "auto")


def test_no_matching_subtitles_is_an_error():
    with pytest.raises(ExtractionError, match="no subtitles"):
        yt.pick_subtitles(info(manual=["de"], auto=[]), ["en.*"])


# --- transcript text ----------------------------------------------------------------------------


def test_repeated_cues_and_empty_events_are_dropped():
    data = json3((0, "Hello"), (2, "Hello"), (3, "\n"), (4, "world"))
    data["events"].append({"tStartMs": 9000})  # no segs
    assert yt.cues_from_json3(data) == [(0.0, "Hello"), (4.0, "world")]


def test_time_markers_every_thirty_seconds():
    cues = [(1.0, "a"), (12.0, "b"), (40.0, "c"), (75.0, "d")]
    assert yt.transcript_markdown(cues).split("\n\n") == [
        "<!-- t: 00:01 -->",
        "a b",
        "<!-- t: 00:40 -->",
        "c",
        "<!-- t: 01:15 -->",
        "d",
    ]


# --- capture ------------------------------------------------------------------------------------


def test_capture_writes_raw_markdown_with_provenance(vault):
    runner = FakeYtDlp(info(manual=["en"]), {"en": CUES})
    path, meta = yt.capture_youtube(URL, vault, runner=runner)

    assert path == vault.root / "raw" / "youtube" / f"intro-to-obsidian-{VID}.md"
    front, body = parse_frontmatter(path.read_text("utf-8"))
    assert front == {
        "title": "Intro to Obsidian",
        "source_type": "youtube",
        "source_url": f"https://www.youtube.com/watch?v={VID}",
        "author": "Some Channel",
        "video_id": VID,
        "upload_date": "2024-01-31",
        "duration_seconds": 754,
        "language": "en",
        "transcript_kind": "manual",
        "captured_at": front["captured_at"],
    }
    assert "<!-- t: 00:01 -->" in body and "Hello and welcome. Today we set up" in body
    assert (meta.title, meta.channel, meta.transcript_kind) == (
        "Intro to Obsidian",
        "Some Channel",
        "manual",
    )


def test_privacy_override_is_recorded(vault):
    runner = FakeYtDlp(info(), {"en": CUES})
    path, _ = yt.capture_youtube(URL, vault, runner=runner, privacy="personal")
    assert parse_frontmatter(path.read_text("utf-8"))[0]["privacy"] == "personal"


def test_runner_gets_list_argv_timeout_and_dashes_before_the_url(vault):
    runner = FakeYtDlp(info(), {"en": CUES})
    yt.capture_youtube(f"https://www.youtube.com/watch?v={VID}&list=PL1&t=9", vault, runner=runner)

    assert len(runner.calls) == 2  # info, then the one chosen subtitle track
    for args, timeout in runner.calls:
        assert isinstance(args, list) and args[0] == "yt-dlp"
        assert args[-2:] == ["--", f"https://www.youtube.com/watch?v={VID}"]  # canonical URL only
        assert timeout == yt.YT_DLP_TIMEOUT
    second = runner.calls[1][0]
    assert second[second.index("--sub-langs") + 1] == "en"
    assert "--write-auto-subs" in second and "--write-subs" not in second


def test_existing_capture_is_not_overwritten_or_refetched(vault):
    runner = FakeYtDlp(info(manual=["en"]), {"en": CUES})
    path, _ = yt.capture_youtube(URL, vault, runner=runner)
    before = path.read_text("utf-8")

    again = FakeYtDlp(info(title="Changed"), {"en": json3((0, "different"))})
    path2, meta = yt.capture_youtube(URL, vault, runner=again)
    assert path2 == path and path.read_text("utf-8") == before
    assert again.calls == []
    assert meta.title == "Intro to Obsidian" and meta.transcript_kind == "manual"


def test_video_without_subtitles_fails_clearly_and_writes_nothing(vault):
    runner = FakeYtDlp(info(manual=[], auto=[]))
    with pytest.raises(ExtractionError, match="no subtitles"):
        yt.capture_youtube(URL, vault, runner=runner)
    assert not (vault.root / "raw" / "youtube").exists()


def test_yt_dlp_failure_message_has_no_tool_output(vault):
    def runner(args, timeout=None):
        raise ExtractionError("yt-dlp failed with exit code 1")

    with pytest.raises(ExtractionError) as err:
        yt.capture_youtube(URL, vault, runner=runner)
    assert "exit code" not in str(err.value) and "age-restricted" in str(err.value)


def test_rejected_url_never_reaches_the_runner(vault):
    runner = FakeYtDlp(info())
    with pytest.raises(UrlRejected):
        yt.capture_youtube(f"https://evil.com/watch?v={VID}", vault, runner=runner)
    assert runner.calls == []


# --- ingest routing -----------------------------------------------------------------------------


def test_youtube_capture_ingests_as_public_youtube_source_under_videos(vault, factory, fake):
    runner = FakeYtDlp(info(manual=["en"]), {"en": CUES})
    path, _ = yt.capture_youtube(URL, vault, runner=runner)

    result = ingest_file(vault, path, provider_factory=factory)

    assert result.status == "ingested"
    page = (vault.root / result.summary_path).read_text("utf-8")
    assert "youtube" in page and "public" in page
    index = (vault.root / "index.md").read_text("utf-8")
    videos = index.split("## Videos")[1].split("\n## ")[0]
    assert "Intro to Obsidian" in videos
    assert "<!-- t: 00:01 -->" in fake.prompts[0]  # the model sees the time markers
    assert ingest_file(vault, path, provider_factory=factory).status == "duplicate"


# --- rate limiting ------------------------------------------------------------------------------


class RateLimitedThenOk(FakeYtDlp):
    def __init__(self, failures, *a, **kw):
        super().__init__(*a, **kw)
        self.failures = failures

    def __call__(self, args, timeout=None):
        if "--sub-langs" in args and self.failures:
            self.failures -= 1
            self.calls.append((args, timeout))
            raise RateLimited("yt-dlp was rate limited (HTTP 429)")
        return super().__call__(args, timeout)


def test_http_429_is_retried_with_waits_then_succeeds(vault):
    runner = RateLimitedThenOk(2, info(), {"en": CUES})
    waits = []
    path, _ = yt.capture_youtube(URL, vault, runner=runner, sleep=waits.append)
    assert path.is_file() and waits == list(yt.RATE_LIMIT_WAITS)


def test_persistent_429_gives_a_rate_limit_message_not_the_private_video_one(vault):
    runner = RateLimitedThenOk(99, info(), {"en": CUES})
    with pytest.raises(ExtractionError, match="rate-limiting") as err:
        yt.capture_youtube(URL, vault, runner=runner, sleep=lambda s: None)
    assert "private" not in str(err.value)
    assert not (vault.root / "raw" / "youtube").exists()
