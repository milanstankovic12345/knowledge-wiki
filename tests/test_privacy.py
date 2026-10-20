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


def _cloud_vault(vault, **kw):
    from scripts.config import ProviderSettings

    vault.provider = ProviderSettings(
        _env_file=None,
        ollama_cloud_api_key="k-secret",
        ollama_cloud_text_model="cloud-model",
        **kw,
    )
    return vault


@pytest.fixture
def cloud_up(monkeypatch):
    from scripts.providers import router

    monkeypatch.setattr(router.OllamaCloudProvider, "health", lambda self: True)
    monkeypatch.setattr(router.OpenAICompatibleProvider, "health", lambda self: True)
    monkeypatch.setattr(router.OllamaLocalProvider, "health", lambda self: True)


@pytest.fixture
def cloud_down(monkeypatch):
    from scripts.providers import router

    monkeypatch.setattr(router.OllamaCloudProvider, "health", lambda self: False)
    monkeypatch.setattr(router.OllamaLocalProvider, "health", lambda self: True)


@pytest.mark.parametrize("requested", ["ollama-cloud", "hybrid"])
def test_public_article_uses_cloud(vault, cloud_up, requested):
    _cloud_vault(vault)
    p = select_provider(vault, "public", "article", "raw/articles/a.md", requested)
    assert (p.name, p.model) == ("ollama-cloud", "cloud-model")


def test_public_article_openai_compatible(vault, cloud_up):
    from scripts.config import ProviderSettings

    vault.provider = ProviderSettings(
        _env_file=None,
        openai_compatible_base_url="https://api.example.com/v1",
        openai_compatible_api_key="k",
        openai_compatible_text_model="m",
    )
    p = select_provider(vault, "public", "article", "raw/articles/a.md", "openai-compatible")
    assert p.name == "openai-compatible"


@pytest.mark.parametrize("requested", ["ollama-cloud", "openai-compatible", "hybrid"])
@pytest.mark.parametrize(
    ("cls", "stype", "path"),
    [
        ("personal", "telegram_text", "raw/telegram/a.md"),
        ("private", "article", "raw/articles/a.md"),
        ("public", "book", "raw/articles/a.md"),  # needs explicit approval
        ("public", "article", "raw/books/a.md"),  # local-only path
    ],
)
def test_private_content_never_reaches_cloud(vault, cloud_up, requested, cls, stype, path):
    _cloud_vault(vault)
    with pytest.raises(CloudBlocked):
        select_provider(vault, cls, stype, path, requested)


def test_public_falls_back_to_local_when_cloud_unavailable(vault, cloud_down):
    _cloud_vault(vault)
    p = select_provider(vault, "public", "article", "raw/articles/a.md", "hybrid")
    assert p.name == "ollama-local"


def test_cloud_without_credentials_is_unhealthy():
    from scripts.providers.ollama_cloud import OllamaCloudProvider

    assert not OllamaCloudProvider("https://ollama.com", "", "m").health()
    assert not OllamaCloudProvider("https://ollama.com", "k", "").health()


def test_both_down_public_fails(vault, monkeypatch):
    from scripts.providers import router

    _cloud_vault(vault)
    monkeypatch.setattr(router.OllamaCloudProvider, "health", lambda self: False)
    monkeypatch.setattr(router.OllamaLocalProvider, "health", lambda self: False)
    with pytest.raises(ProviderUnavailable):
        select_provider(vault, "public", "article", "raw/articles/a.md", "hybrid")


def test_cloud_errors_do_not_leak_key_or_prompt(monkeypatch):
    import httpx

    from scripts.providers.openai_compatible import OpenAICompatibleProvider

    def boom(*a, **k):
        raise httpx.ConnectError("Bearer k-secret SECRET-PROMPT")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(ProviderUnavailable) as exc:
        OpenAICompatibleProvider("https://x/v1", "k-secret", "m").generate("s", "SECRET-PROMPT")
    assert "k-secret" not in str(exc.value) and "SECRET-PROMPT" not in str(exc.value)


def test_cloud_provenance_recorded_in_source_page(vault, article, cloud_up, monkeypatch, fake):
    from scripts.providers import router
    from scripts.storage import parse_frontmatter
    from scripts.wiki.ingest import ingest_file

    _cloud_vault(vault, llm_provider="ollama-cloud")
    monkeypatch.setattr(
        router.OllamaCloudProvider,
        "generate",
        lambda self, s, p, schema=None: __import__("json").dumps(fake.analysis.model_dump()),
    )
    result = ingest_file(vault, article, select_provider)
    meta, _ = parse_frontmatter((vault.root / result.summary_path).read_text("utf-8"))
    assert (meta["llm_provider"], meta["llm_model"]) == ("ollama-cloud", "cloud-model")
    assert "k-secret" not in (vault.root / "log.md").read_text("utf-8")


def test_local_down_fails_safely_without_cloud(vault):
    vault.provider.ollama_local_url = "http://127.0.0.1:9"  # nothing listens here
    with pytest.raises(ProviderUnavailable):
        select_provider(vault, "public", "article", "raw/articles/a.md", "local")
