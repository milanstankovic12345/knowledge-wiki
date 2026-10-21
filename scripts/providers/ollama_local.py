"""Local Ollama text provider."""

from __future__ import annotations

from typing import Any

import httpx
import ollama

from scripts.providers.base import ProviderUnavailable

# A structured-output generation can loop forever (the JSON string never closes) and keep shifting
# the context window. Cap the output and the wait so a runaway fails fast instead of hanging.
MAX_OUTPUT_TOKENS = 2048
# Ollama's default window is small and silently truncates long chunks; ask for one that fits
# context_chars plus the output cap.
DEFAULT_NUM_CTX = 8192


class OllamaLocalProvider:
    name = "ollama-local"

    def __init__(
        self,
        url: str,
        model: str,
        keep_alive: str = "30s",
        timeout: float = 180.0,
        num_ctx: int = DEFAULT_NUM_CTX,
    ):
        self.model = model
        self._keep_alive = keep_alive
        self._num_ctx = num_ctx
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

    def generate(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        try:
            response = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                format=schema,
                think=False,
                keep_alive=self._keep_alive,
                options={
                    "temperature": 0.2,
                    "num_predict": MAX_OUTPUT_TOKENS,
                    "num_ctx": self._num_ctx,
                },
            )
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            # Never include prompt text in the error: it is source content.
            raise ProviderUnavailable(f"ollama request failed: {type(exc).__name__}") from exc
        return response.message.content or ""
