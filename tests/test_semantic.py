import pytest

from scripts.providers.base import ProviderUnavailable
from scripts.telegram.query import search_wiki
from scripts.wiki.semantic import sync_embeddings

PAGES = {
    "wiki/topics/cost-optimization.md": (
        "---\ntitle: Cost optimization\n---\n\nKeep spending low.\n"
    ),
    "wiki/topics/gardening.md": "---\ntitle: Gardening\n---\n\nPlant tomatoes in spring.\n",
}


class FakeEmbedder:
    """Maps meaning groups to axes so tests control similarity without a model."""

    model = "fake-embed"

    def __init__(self):
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        out = []
        for t in texts:
            t = t.lower()
            money = any(w in t for w in ("cost", "spending", "cheaper", "budget"))
            plants = any(w in t for w in ("tomato", "garden"))
            out.append([1.0 if money else 0.0, 1.0 if plants else 0.0, 0.1])
        return out


class DownEmbedder:
    model = "down"

    def embed(self, texts):
        raise ProviderUnavailable("embedding request failed: ConnectError")


@pytest.fixture
def wiki(vault):
    (vault.root / "data").mkdir(exist_ok=True)
    for rel, text in PAGES.items():
        path = vault.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")
    return vault


def test_paraphrase_finds_page_with_no_shared_words(wiki):
    assert search_wiki(wiki, "make everything cheaper", 5) == []  # keyword search misses it
    hits = search_wiki(wiki, "make everything cheaper", 5, FakeEmbedder())
    assert [h.path for h in hits] == ["wiki/topics/cost-optimization.md"]


def test_sync_only_reembeds_changed_pages_and_drops_removed(wiki):
    emb = FakeEmbedder()
    assert set(sync_embeddings(wiki, emb)) == set(PAGES)
    sync_embeddings(wiki, emb)
    assert len(emb.calls) == 1  # second sync found nothing stale
    path = wiki.root / "wiki/topics/gardening.md"
    path.write_text(path.read_text("utf-8") + "More tomatoes.\n", "utf-8")
    sync_embeddings(wiki, emb)
    assert len(emb.calls[-1]) == 1
    (wiki.root / "wiki/topics/cost-optimization.md").unlink()
    assert set(sync_embeddings(wiki, emb)) == {"wiki/topics/gardening.md"}


def test_down_embedder_falls_back_to_keyword_results(wiki):
    keyword = search_wiki(wiki, "tomatoes spring", 5)
    fallback = search_wiki(wiki, "tomatoes spring", 5, DownEmbedder())
    assert keyword and [h.path for h in fallback] == [h.path for h in keyword]


def test_keyword_ranking_unchanged_without_embedder(wiki):
    assert search_wiki(wiki, "gardening", 5)[0].path == "wiki/topics/gardening.md"
