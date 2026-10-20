from scripts.wiki.lint import format_report, lint, run_lint

SOURCE = (
    "---\ntitle: S\ntype: source-summary\nsource_type: article\nraw_path: raw/a.md\n"
    "captured_at: '2026-01-01'\ncontent_hash: abc\nprivacy: public\nllm_model: m\n"
    "processed_at: '2026-01-01'\n---\n\n# S\n\n## Contradictions\n\n- None recorded.\n"
)
INDEX = (
    "# Index\n\n## Topics\n\n- [[topics/good]]\n- [[sources/s]]\n\n"
    "## Wiki health\n\n- Last lint:\n"
)


def write(vault, rel, text):
    path = vault.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def healthy(vault):
    write(vault, "index.md", INDEX)
    write(vault, "log.md", "# Log\n")
    write(vault, "wiki/sources/s.md", SOURCE)
    write(
        vault,
        "wiki/topics/good.md",
        "---\ntitle: Good\ntype: topic\nsources:\n- sources/s\n---\n\nFrom [[sources/s]].\n",
    )


def kinds(vault):
    return {(f.kind, f.page) for f in lint(vault).findings}


def test_clean_wiki_has_no_findings(vault):
    healthy(vault)
    report = lint(vault)
    assert report.findings == [] and report.pages == 2
    assert "healthy" in format_report(report)


def test_each_defect_is_reported(vault):
    healthy(vault)
    write(vault, "index.md", INDEX + "- [[topics/ghost]]\n")
    write(vault, "wiki/topics/orphan.md", "---\ntype: topic\nsources: [sources/s]\n---\n\nHi\n")
    write(vault, "wiki/topics/nosrc.md", "---\ntype: topic\n---\n\nLinks [[topics/nowhere]]\n")
    write(vault, "wiki/sources/bad.md", "---\ntype: source-summary\nsource_type: article\n---\n\n")
    write(
        vault,
        "wiki/topics/conflict.md",
        "---\ntype: topic\nsources: [sources/s]\n---\n\nSee [[sources/s]]\n\n"
        "## Contradictions\n\nA says X, B says Y.\n",
    )
    found = kinds(vault)
    assert ("stale-index", "index.md") in found
    assert ("orphan", "wiki/topics/orphan.md") in found
    assert ("no-source", "wiki/topics/nosrc.md") in found
    assert ("broken-link", "wiki/topics/nosrc.md") in found
    assert ("missing-provenance", "wiki/sources/bad.md") in found
    assert ("open-contradiction", "wiki/topics/conflict.md") in found
    assert ("open-contradiction", "wiki/sources/s.md") not in found  # "None recorded." is empty


def test_linked_but_unlisted_page_is_not_indexed_not_orphan(vault):
    healthy(vault)
    write(vault, "wiki/topics/extra.md", "---\ntype: topic\nsources: [sources/s]\n---\n\nHi\n")
    good = "---\ntype: topic\nsources: [sources/s]\n---\n\n[[topics/extra]]\n"
    write(vault, "wiki/topics/good.md", good)
    assert ("not-indexed", "wiki/topics/extra.md") in kinds(vault)


def test_run_lint_records_result_and_never_edits_pages(vault):
    healthy(vault)
    before = {p: p.read_text("utf-8") for p in (vault.root / "wiki").rglob("*.md")}
    run_lint(vault)
    assert {p: p.read_text("utf-8") for p in before} == before
    assert "(0 issues)" in (vault.root / "index.md").read_text("utf-8")
    assert "lint | 2 pages" in (vault.root / "log.md").read_text("utf-8")
