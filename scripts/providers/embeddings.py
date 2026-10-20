"""Local Ollama embeddings. Wiki pages are personal, so there is deliberately no cloud variant."""

from __future__ import annotations

import httpx
import ollama

from scripts.providers.base import ProviderUnavailable


class OllamaEmbedder:
    name = "ollama-local"

    def __init__(self, url: str, model: str, keep_alive: str = "30s", timeout: float = 120.0):
        self.model = model
        self._keep_alive = keep_alive
        self._url = url.rstrip("/")
        self._client = ollama.Client(host=self._url, timeout=timeout)

    def health(self) -> bool:
        try:
            tags = httpx.get(f"{self._url}/api/tags", timeout=5.0)
            tags.raise_for_status()
        except httpx.HTTPError:
            return False
        names = {m.get("name", "") for m in tags.json().get("models", [])}
        return self.model in names or f"{self.model}:latest" in names

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self._client.embed(
                model=self.model, input=texts, keep_alive=self._keep_alive
            )
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            # Never include the text in the error: it is wiki content.
            raise ProviderUnavailable(f"embedding request failed: {type(exc).__name__}") from exc
        return [list(v) for v in response.embeddings]
