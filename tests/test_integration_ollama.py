import pytest

from scripts.config import load_vault
from scripts.models import Analysis
from scripts.providers.router import select_provider
from scripts.wiki.ingest import analyse

pytestmark = pytest.mark.integration


def test_live_ollama_returns_valid_analysis():
    vault = load_vault()
    provider = select_provider(vault, "public", "article", "raw/articles/x.md", "local")
    text = (
        "Spaced repetition reviews material at increasing intervals. "
        "The author argues linked notes are easier to rediscover than isolated ones."
    )
    result = analyse(provider, text, 24000)
    assert isinstance(result, Analysis)
    assert result.summary
