from types import SimpleNamespace

import httpx
import pytest

from scripts.providers.base import ProviderUnavailable
from scripts.providers.ollama_local import DEFAULT_NUM_CTX, MAX_OUTPUT_TOKENS, OllamaLocalProvider


def provider_with(chat):
    p = OllamaLocalProvider("http://127.0.0.1:11434", "m")
    p._client = SimpleNamespace(chat=chat)
    return p


def test_generation_is_capped_so_a_runaway_cannot_hang():
    seen = {}

    def chat(**kw):
        seen.update(kw)
        return SimpleNamespace(message=SimpleNamespace(content="{}"))

    provider_with(chat).generate("s", "p", {"type": "object"})
    assert seen["options"]["num_predict"] == MAX_OUTPUT_TOKENS


def test_context_window_is_requested_so_long_chunks_are_not_truncated():
    seen = {}

    def chat(**kw):
        seen.update(kw)
        return SimpleNamespace(message=SimpleNamespace(content="{}"))

    provider_with(chat).generate("s", "p")
    assert seen["options"]["num_ctx"] == DEFAULT_NUM_CTX


def test_timeout_is_reported_as_provider_unavailable():
    def chat(**kw):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(ProviderUnavailable):
        provider_with(chat).generate("s", "p")
