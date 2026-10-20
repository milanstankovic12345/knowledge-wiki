import pytest

from scripts.providers.base import ProviderUnavailable
from scripts.wiki.link import apply_link, suggest_links

VECTORS = {
    "alpha": [1.0, 0.0, 0.0],
    "beta": [0.95, 0.1, 0.0],  # close to alpha
    "gamma": [0.0, 1.0, 0.0],  # unrelated
    "delta": [0.97, 0.05, 0.0],  # close to alpha and beta
}


class FakeEmbedder:
    model = "fake-embed"

    def __init__(self, down=False):
        self.down = down

    def embed(self, texts):
        if self.down:
            raise ProviderUnavailable("down")
        return [VECTORS[t.split("\n", 1)[0].lower()] for t in texts]


def page(vault, rel, title, body=""):
    path = vault.root / "wiki" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: {title}\ntype: topic\n---\n\n{body}\n", "utf-8")
    return path


@pytest.fixture
def wiki(vault):
    (vault.root / "log.md").write_text("# Log\n", "utf-8")
    for name in ("alpha", "beta", "gamma"):
        page(vault, f"topics/{name}.md", name.title())
    return vault


def pairs(found):
    return {(s.a, s.b) for s in found}


def test_suggests_similar_unlinked_pair_only(wiki):
    found = suggest_links(wiki, FakeEmbedder())
    assert pairs(found) == {("topics/alpha", "topics/beta")}
    assert 0.9 < found[0].similarity <= 1.0


def test_skips_pairs_already_linked_in_either_direction(wiki):
    page(wiki, "topics/alpha.md", "Alpha", "See [[topics/beta]]")
    assert suggest_links(wiki, FakeEmbedder()) == []
    page(wiki, "topics/alpha.md", "Alpha")
    page(wiki, "topics/beta.md", "Beta", "See [[alpha]]")  # bare stem form also counts
    assert suggest_links(wiki, FakeEmbedder()) == []


def test_pairs_are_deduped_ranked_and_limited(wiki):
    page(wiki, "topics/delta.md", "Delta")
    found = suggest_links(wiki, FakeEmbedder())
    assert len(found) == 3 and len(pairs(found)) == 3  # (a,b) never appears as (b,a) too
    assert [s.similarity for s in found] == sorted((s.similarity for s in found), reverse=True)
    assert len(suggest_links(wiki, FakeEmbedder(), limit=1)) == 1


def test_threshold_comes_from_settings(wiki):
    wiki.settings["link"] = {"min_similarity": 0.999}
    assert suggest_links(wiki, FakeEmbedder()) == []


def test_embedder_down_raises(wiki):
    with pytest.raises(ProviderUnavailable):
        suggest_links(wiki, FakeEmbedder(down=True))


def test_apply_links_both_ways_creates_section_and_logs(wiki):
    assert apply_link(wiki, "topics/alpha", "topics/beta") is True
    alpha = (wiki.root / "wiki/topics/alpha.md").read_text("utf-8")
    beta = (wiki.root / "wiki/topics/beta.md").read_text("utf-8")
    assert "## Related topics\n\n- [[topics/beta]]" in alpha
    assert "- [[topics/alpha]]" in beta
    assert "link | topics/alpha <-> topics/beta" in (wiki.root / "log.md").read_text("utf-8")
    assert suggest_links(wiki, FakeEmbedder()) == []


def test_apply_appends_to_existing_section_and_is_idempotent(wiki):
    body = "## Related topics\n\n- [[topics/gamma]]\n\n## Sources\n\n- s"
    page(wiki, "topics/alpha.md", "Alpha", body)
    apply_link(wiki, "topics/alpha", "topics/beta")
    text = (wiki.root / "wiki/topics/alpha.md").read_text("utf-8")
    assert text.index("[[topics/gamma]]") < text.index("[[topics/beta]]") < text.index("## Sources")
    snapshot = {p: p.read_text("utf-8") for p in wiki.root.rglob("*.md")}
    assert apply_link(wiki, "topics/alpha", "topics/beta") is False
    assert {p: p.read_text("utf-8") for p in snapshot} == snapshot  # no second write or log entry


@pytest.mark.parametrize("bad", ["../index", "topics/missing", "../../etc/passwd"])
def test_apply_rejects_paths_outside_wiki_or_missing(wiki, bad):
    (wiki.root / "index.md").write_text("# Index\n", "utf-8")
    with pytest.raises(ValueError):
        apply_link(wiki, "topics/alpha", bad)
    assert (wiki.root / "index.md").read_text("utf-8") == "# Index\n"
    assert "[[" not in (wiki.root / "wiki/topics/alpha.md").read_text("utf-8")
