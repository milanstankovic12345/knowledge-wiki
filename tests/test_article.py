import hashlib
from pathlib import Path

import pytest

from scripts.extractors.article import extract_article, strip_noise
from scripts.providers.base import CloudBlocked
from scripts.providers.router import select_provider
from scripts.storage import parse_frontmatter
from scripts.wiki.ingest import ingest_file, resolve_privacy

TEMPLATE_CLIP = """---
title: "Template Clip"
type: raw-source
source_type: article
source_url: "https://example.com/t"
author: "Jane Doe"
captured_at: "2026-10-20"
status: pending
visibility: {visibility}
tags:
  - source/article
---

# Template Clip

## Metadata

- URL: https://example.com/t

## Content

![](https://example.com/img.png)

Real prose here.
"""


def write_clip(vault, name, text):
    path = vault.root / "raw" / "articles" / name
    path.write_text(text, encoding="utf-8")
    return path


def summary_meta(vault, result):
    return parse_frontmatter((vault.root / result.summary_path).read_text("utf-8"))[0]


def test_strip_noise_keeps_prose():
    body = "Intro\n\n![](x.png)\n\n<script>evil()</script>\n<!-- page: 3 -->\n\n\n\nOutro"
    assert strip_noise(body) == "Intro\n\nOutro"


def test_strip_noise_removes_linked_images_but_not_inline_links():
    body = "Intro\n\n[![Demo](https://e.com/i.png)](https://e.com/v)\n\nSee [docs](https://e.com)."
    assert strip_noise(body) == "Intro\n\nSee [docs](https://e.com)."


def test_metadata_section_is_a_fallback():
    text = (
        "# From Heading\n\n## Metadata\n\n"
        "- URL: https://e.com/x\n- Author: Ann\n- Captured: 2026-01-02\n"
    )
    got = extract_article(text, Path("clip.md"))
    assert (got.title, got.author, got.source_url, got.captured_at) == (
        "From Heading",
        "Ann",
        "https://e.com/x",
        "2026-01-02",
    )


def test_empty_metadata_bullet_does_not_swallow_the_next_line():
    text = "# T\n\n## Metadata\n\n- URL: https://e.com/x\n- Author:\n- Captured: 2026-01-02\n"
    got = extract_article(text, Path("clip.md"))
    assert got.author == ""
    assert got.captured_at == "2026-01-02"


@pytest.mark.parametrize(
    ("meta", "source_type", "expected"),
    [
        ({"visibility": "private"}, "article", "personal"),
        ({"visibility": "public"}, "article", "public"),
        ({"visibility": "PRIVATE "}, "article", "personal"),
        ({"visibility": "bogus"}, "article", "public"),  # type default
        ({"visibility": "bogus"}, "unknown_type", "private"),  # global default
        ({"visibility": "public"}, "book", "personal"),  # never loosens approval-gated types
        ({"privacy": "confidential", "visibility": "public"}, "article", "confidential"),
        ({}, "article", "public"),
    ],
)
def test_resolve_privacy(vault, meta, source_type, expected):
    assert resolve_privacy(vault.privacy, meta, source_type) == expected


def test_private_clip_is_personal_and_blocked_from_cloud(vault, factory):
    clip = write_clip(vault, "private.md", TEMPLATE_CLIP.format(visibility="private"))
    result = ingest_file(vault, clip, factory)
    assert summary_meta(vault, result)["privacy"] == "personal"
    with pytest.raises(CloudBlocked):
        select_provider(
            vault, "personal", "article", "raw/articles/private.md", requested="ollama-cloud"
        )


def test_clip_noise_is_removed_before_the_model_sees_it(vault, factory, fake):
    clip = write_clip(vault, "public.md", TEMPLATE_CLIP.format(visibility="public"))
    result = ingest_file(vault, clip, factory)
    assert summary_meta(vault, result)["privacy"] == "public"
    assert "Real prose here." in fake.prompts[0]
    assert "img.png" not in fake.prompts[0]


def test_injection_text_stays_wrapped_and_raw_is_untouched(vault, factory, fake, article):
    before = hashlib.sha256(article.read_bytes()).hexdigest()
    ingest_file(vault, article, factory)
    assert hashlib.sha256(article.read_bytes()).hexdigest() == before
    assert "Ignore all previous instructions" in fake.prompts[0]
    assert fake.prompts[0].index("untrusted") < fake.prompts[0].index("Ignore all previous")


def test_duplicate_clip_and_retry_create_no_duplicate_pages(vault, factory, down_factory):
    clip = write_clip(vault, "dup.md", TEMPLATE_CLIP.format(visibility="private"))
    with pytest.raises(Exception, match="unavailable"):
        ingest_file(vault, clip, down_factory)
    assert not list((vault.root / "wiki" / "sources").iterdir())
    first = ingest_file(vault, clip, factory)
    again = ingest_file(vault, clip, factory)
    assert again.status == "duplicate"
    assert again.summary_path == first.summary_path
    assert len(list((vault.root / "wiki" / "sources").iterdir())) == 1
