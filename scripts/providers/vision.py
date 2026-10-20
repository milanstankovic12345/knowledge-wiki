"""Local Ollama vision provider (image description)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import httpx
import ollama

from scripts.providers.base import ProviderUnavailable


class VisionProvider(Protocol):
    name: str
    model: str

    def health(self) -> bool: ...

    def describe(self, image: Path, prompt: str) -> str: ...


class OllamaVisionProvider:
    name = "ollama-local"

    def __init__(self, url: str, model: str, keep_alive: str = "30s", timeout: float = 600.0):
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

    def describe(self, image: Path, prompt: str) -> str:
        try:
            response = self._client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt, "images": [str(image)]}],
                think=False,
                keep_alive=self._keep_alive,
                options={"temperature": 0.1},
            )
        except (ollama.ResponseError, httpx.HTTPError, ConnectionError) as exc:
            raise ProviderUnavailable(
                f"ollama vision request failed: {type(exc).__name__}"
            ) from exc
        return (response.message.content or "").strip()
