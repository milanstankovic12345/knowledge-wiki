"""OpenAI-compatible text provider (chat completions over httpx). Router-gated like all cloud."""

from __future__ import annotations

from typing import Any

import httpx

from scripts.providers.base import ProviderUnavailable


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 600.0):
        self.model = model
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._timeout = timeout

    def health(self) -> bool:
        if not (self.model and self._base):
            return False
        try:
            r = httpx.get(f"{self._base}/models", headers=self._headers, timeout=10.0)
            r.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    def generate(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "analysis", "schema": schema},
            }
        try:
            r = httpx.post(
                f"{self._base}/chat/completions",
                headers=self._headers,
                json=body,
                timeout=self._timeout,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or ""
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ProviderUnavailable(
                f"openai-compatible request failed: {type(exc).__name__}"
            ) from exc
