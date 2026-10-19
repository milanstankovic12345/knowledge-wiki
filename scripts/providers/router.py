"""Privacy-aware provider selection. Enforces `config/privacy.yaml` before any LLM call."""

from __future__ import annotations

from typing import Any

from scripts.config import Vault
from scripts.providers.base import CloudBlocked, ProviderUnavailable, TextProvider
from scripts.providers.ollama_local import OllamaLocalProvider

CLOUD_PROVIDERS = {"ollama-cloud", "openai-compatible", "hybrid"}


def cloud_allowed(
    privacy_cfg: dict[str, Any],
    privacy_class: str,
    source_type: str,
    raw_path: str,
    approved: bool = False,
) -> bool:
    """True only if policy permits sending this source to a cloud provider."""
    cls = privacy_cfg.get("classifications", {}).get(privacy_class)
    if not cls or not cls.get("allow_cloud", False):
        return False
    for local_only in privacy_cfg.get("local_only_paths", []):
        if raw_path.replace("\\", "/").startswith(local_only.rstrip("/") + "/"):
            return False
    needs_approval = source_type in privacy_cfg.get("cloud_requires_explicit_approval", [])
    return approved or not needs_approval


def select_provider(
    vault: Vault,
    privacy_class: str,
    source_type: str,
    raw_path: str,
    requested: str | None = None,
) -> TextProvider:
    """Pick a provider. Local content never falls back to cloud, even if local is down."""
    requested = requested or vault.provider.llm_provider
    if requested in CLOUD_PROVIDERS and not cloud_allowed(
        vault.privacy, privacy_class, source_type, raw_path
    ):
        raise CloudBlocked(
            f"source is classified {privacy_class!r}; cloud processing is disabled. "
            "Use local processing or explicitly approve cloud use for this source."
        )
    if requested in CLOUD_PROVIDERS:
        # Policy would allow it, but cloud providers arrive in Phase 7.
        raise ProviderUnavailable(f"provider {requested!r} is not implemented yet")
    if requested != "local":
        raise ProviderUnavailable(f"unknown provider {requested!r}")

    provider = OllamaLocalProvider(
        vault.provider.ollama_local_url,
        vault.provider.ollama_local_text_model,
        keep_alive=str(vault.settings.get("models", {}).get("keep_alive", "30s")),
    )
    if not provider.health():
        raise ProviderUnavailable("local Ollama is unavailable or the model is not pulled")
    return provider
