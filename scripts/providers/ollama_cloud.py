"""Ollama Cloud text provider. Only reachable through the privacy-checked router."""

from __future__ import annotations

from typing import Any

import httpx
import ollama

from scripts.providers.base import ProviderUnavailable


class OllamaCloudProvider:
    name = "ollama-cloud"

    def __init__(self, url: str, api_key: str, model: str, timeout: float = 600.0):
        self.model = model
        self._has_key = bool(api_key)
        self._url = url.rstrip("/").removesuffix("/api")
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._client = ollama.Client(host=self._url, headers=self._headers, timeout=timeout)

    def health(self) -> bool:
        if not (self.model and self._has_key):
            return False
        try:
            r = httpx.get(f"{self._url}/api/tags", headers=self._headers, timeout=10.0)
            r.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

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
                options={"temperature": 0.2},
            )
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            # Never include prompt text or headers in the error: they hold source content and keys.
            raise ProviderUnavailable(f"ollama cloud request failed: {type(exc).__name__}") from exc
        return response.message.content or ""
