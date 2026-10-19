import pytest

from scripts.providers.base import CloudBlocked, ProviderUnavailable
from scripts.providers.router import cloud_allowed, select_provider


def test_public_article_cloud_allowed(vault):
    assert cloud_allowed(vault.privacy, "public", "article", "raw/articles/a.md")


@pytest.mark.parametrize("cls", ["personal", "confidential", "restricted", "private", "bogus"])
def test_non_public_cloud_blocked(vault, cls):
    assert not cloud_allowed(vault.privacy, cls, "article", "raw/articles/a.md")


def test_local_only_path_blocked_even_if_public(vault):
    assert not cloud_allowed(vault.privacy, "public", "article", "raw/books/a.md")


def test_explicit_approval_source_types(vault):
    assert not cloud_allowed(vault.privacy, "public", "book", "raw/articles/a.md")
    assert cloud_allowed(vault.privacy, "public", "book", "raw/articles/a.md", approved=True)


def test_private_source_cloud_request_blocked(vault):
    with pytest.raises(CloudBlocked):
        select_provider(vault, "personal", "telegram_text", "raw/telegram/a.md", "ollama-cloud")


def test_public_cloud_request_not_implemented_yet(vault):
    with pytest.raises(ProviderUnavailable):
        select_provider(vault, "public", "article", "raw/articles/a.md", "ollama-cloud")


def test_local_down_fails_safely_without_cloud(vault):
    vault.provider.ollama_local_url = "http://127.0.0.1:9"  # nothing listens here
    with pytest.raises(ProviderUnavailable):
        select_provider(vault, "public", "article", "raw/articles/a.md", "local")
