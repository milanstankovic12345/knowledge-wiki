import os
from types import SimpleNamespace

from scripts import batch
from scripts.batch import Outcome
from scripts.extractors.tools import ExtractionError
from scripts.providers.base import ProviderUnavailable
from scripts.security import PathRejected

YT = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
ART = "https://example.com/post"
OLD = 1_000_000.0  # an mtime far in the past, so files count as settled


def age(path, mtime=OLD):
    os.utime(path, (mtime, mtime))
    return path


class Recorder:
    """A fake ingest_item: records calls and returns canned outcomes by item."""

    def __init__(self, fail=(), unavailable=()):
        self.calls, self.fail, self.unavailable = [], set(fail), set(unavailable)

    def __call__(self, vault, item):
        self.calls.append(item)
        if item in self.unavailable:
            return Outcome(item, "unavailable", "down")
        if item in self.fail:
            return Outcome(item, "failed", "boom")
        return Outcome(item, "ingested")


# --- parsing and collecting ---------------------------------------------------------------------


def test_url_list_ignores_comments_blanks_and_duplicates():
    text = f"# my queue\n\n{YT}\nread this: {ART} please\n{YT}\nnot a url\n"
    assert batch.parse_url_list(text) == [YT, ART]


def test_collect_reads_url_lists_folders_and_dedupes(vault):
    lst = vault.root / "urls.txt"
    lst.write_text(f"{YT}\n{ART}\n", "utf-8")
    articles = vault.root / "raw" / "articles"
    (articles / "a.md").write_text("x", "utf-8")
    (articles / "b.png.caption.txt").write_text("x", "utf-8")  # sidecar, not a source
    (articles / "c.exe").write_text("x", "utf-8")

    items = batch.collect_items(vault, [str(lst), "raw/articles", YT])

    assert items == [YT, ART, str(articles / "a.md")]


def test_a_txt_file_inside_raw_is_a_source_not_a_url_list(vault):
    note = vault.root / "raw" / "articles" / "n.txt"
    note.write_text(f"{YT}\n", "utf-8")
    assert batch.collect_items(vault, [str(note)]) == [str(note)]
    assert batch.url_list_path(vault, str(note)) is None


def test_recursive_folder_collection(vault):
    nested = vault.root / "raw" / "articles" / "deep"
    nested.mkdir()
    (nested / "x.md").write_text("x", "utf-8")
    assert batch.collect_items(vault, ["raw/articles"]) == []
    assert batch.collect_items(vault, ["raw/articles"], recursive=True) == [str(nested / "x.md")]


# --- ingest_item dispatch -----------------------------------------------------------------------


def dispatch(vault, item, ingest=None, yt_error=None):
    seen = []

    def capture_yt(url, v):
        seen.append(("yt", url))
        if yt_error:
            raise yt_error
        return "raw/youtube/x.md", SimpleNamespace()

    def capture_art(url, v):
        seen.append(("article", url))
        return "raw/articles/x.md"

    ingest = ingest or (lambda v, p: SimpleNamespace(status="ingested"))
    out = batch.ingest_item(vault, item, capture_yt, capture_art, ingest)
    return out, seen


def test_dispatch_routes_by_kind(vault):
    assert dispatch(vault, YT)[1] == [("yt", YT)]
    assert dispatch(vault, ART)[1] == [("article", ART)]
    paths = []
    out, seen = dispatch(
        vault,
        "raw/articles/a.md",
        lambda v, p: paths.append(p) or SimpleNamespace(status="duplicate"),
    )
    assert (out.status, seen, paths) == ("duplicate", [], ["raw/articles/a.md"])


def test_failures_become_outcomes_not_exceptions(vault):
    assert dispatch(vault, YT, yt_error=ExtractionError("no subtitles"))[0].status == "failed"
    assert dispatch(vault, YT, yt_error=ProviderUnavailable("down"))[0].status == "unavailable"
    assert dispatch(vault, YT, yt_error=PathRejected("nope"))[0].status == "rejected"
    out = dispatch(vault, YT, yt_error=RuntimeError("secret text"))[0]
    assert (
        out.status == "failed" and "secret text" not in out.detail and "RuntimeError" in out.detail
    )


# --- batch run ----------------------------------------------------------------------------------


def test_one_failure_does_not_stop_the_batch(vault):
    rec = Recorder(fail=[YT])
    lines = []
    outcomes = batch.run_items(vault, [YT, ART], lines.append, rec)

    assert rec.calls == [YT, ART]
    assert [o.status for o in outcomes] == ["failed", "ingested"]
    assert batch.summary(outcomes) == "1 failed, 1 ingested"
    assert lines[0].startswith("[1/2] failed:") and "boom" in lines[0]


def test_failed_urls_are_saved_next_to_the_list(vault):
    lst = vault.root / "urls.txt"
    lst.write_text(f"{YT}\n{ART}\n", "utf-8")
    outcomes = batch.run_items(vault, [YT, ART], lambda s: None, Recorder(fail=[ART]))

    out = batch.write_failed_list(lst, outcomes)

    assert out.name == "urls.txt.failed.txt" and out.read_text("utf-8") == ART + "\n"
    assert lst.read_text("utf-8") == f"{YT}\n{ART}\n"  # the original is untouched
    assert batch.write_failed_list(lst, [Outcome(YT, "ingested")]) is None


# --- watch cycle --------------------------------------------------------------------------------


def make_article(vault, name="a.md", text="x"):
    path = vault.root / "raw" / "articles" / name
    path.write_text(text, "utf-8")
    return age(path)


def cycle(vault, rec, attempted, now=OLD + 3600):
    return batch.run_cycle(vault, attempted, now=now, report=lambda s: None, ingest=rec)


def test_new_article_is_ingested_once(vault):
    path = make_article(vault)
    rec, attempted = Recorder(), {}
    cycle(vault, rec, attempted)
    cycle(vault, rec, attempted)
    assert rec.calls == [str(path)]


def test_file_still_being_written_is_skipped(vault):
    make_article(vault)
    rec = Recorder()
    cycle(vault, rec, {}, now=OLD + 1)  # modified one second ago
    assert rec.calls == []


def test_failed_file_is_retried_only_after_it_changes(vault):
    path = make_article(vault)
    rec, attempted = Recorder(fail=[str(path)]), {}
    cycle(vault, rec, attempted)
    cycle(vault, rec, attempted)
    assert rec.calls == [str(path)]  # no hot loop on a broken file

    age(path, OLD + 100)  # edited
    cycle(vault, rec, attempted)
    assert rec.calls == [str(path), str(path)]


def test_provider_down_stops_the_cycle_and_retries_next_time(vault):
    first, second = make_article(vault, "a.md"), make_article(vault, "b.md")
    rec, attempted = Recorder(unavailable=[str(first)]), {}
    cycle(vault, rec, attempted)
    assert rec.calls == [str(first)]  # b.md was not touched

    rec.unavailable.clear()
    cycle(vault, rec, attempted)
    assert rec.calls == [str(first), str(first), str(second)]


def test_inbox_list_moves_to_processed_when_everything_succeeds(vault):
    pending = vault.root / "inbox" / "pending"
    pending.mkdir(parents=True)
    (pending / "q.txt").write_text(f"{YT}\n{ART}\n", "utf-8")
    age(pending / "q.txt")
    rec = Recorder()
    cycle(vault, rec, {})

    assert rec.calls == [YT, ART]
    assert not (pending / "q.txt").exists()
    assert (vault.root / "inbox" / "processed" / "q.txt").is_file()


def test_inbox_list_with_failures_keeps_only_failed_urls_in_failed(vault):
    pending = vault.root / "inbox" / "pending"
    pending.mkdir(parents=True)
    (pending / "q.txt").write_text(f"{YT}\n{ART}\n", "utf-8")
    age(pending / "q.txt")
    cycle(vault, Recorder(fail=[ART]), {})

    moved = vault.root / "inbox" / "failed" / "q.txt"
    assert moved.read_text("utf-8") == ART + "\n"
    assert not (pending / "q.txt").exists()


def test_inbox_list_stays_pending_when_provider_is_down(vault):
    pending = vault.root / "inbox" / "pending"
    pending.mkdir(parents=True)
    (pending / "q.txt").write_text(f"{YT}\n{ART}\n", "utf-8")
    age(pending / "q.txt")
    rec = Recorder(unavailable=[YT])
    cycle(vault, rec, {})

    assert rec.calls == [YT]  # stopped at the first unavailable item
    assert (pending / "q.txt").read_text("utf-8") == f"{YT}\n{ART}\n"


def test_watch_loop_runs_the_requested_cycles(vault):
    make_article(vault)
    slept, lines = [], []
    batch.watch(vault, interval=7, report=lines.append, sleep=slept.append, max_cycles=2)
    assert slept == [7]


def test_pause_only_between_consecutive_youtube_items(vault):
    slept = []
    other = "https://youtu.be/AAAAAAAAAAA"
    batch.run_items(
        vault, [YT, other, ART, YT], lambda s: None, Recorder(), pause=8, sleep=slept.append
    )
    assert slept == [8]
