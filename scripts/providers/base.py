"""Provider interface for text generation."""

from __future__ import annotations

from typing import Any, Protocol


class ProviderUnavailable(RuntimeError):
    """The provider cannot serve the request (down, missing model, not implemented)."""


class CloudBlocked(PermissionError):
    """Privacy policy forbids sending this source to a cloud provider."""


class TextProvider(Protocol):
    name: str
    model: str

    def health(self) -> bool: ...

    def generate(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        """Return the model's text. With `schema`, the text is JSON matching it."""
        ...
