"""Vault configuration: YAML settings, privacy policy and provider environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class ProviderSettings(BaseSettings):
    """Provider selection and endpoints. Values come from the environment or `.env`."""

    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    llm_provider: str = "local"
    ollama_local_url: str = "http://127.0.0.1:11434"
    ollama_local_text_model: str = "qwen3:8b"
    ollama_local_vision_model: str = "qwen3-vl:8b"
    ollama_cloud_url: str = "https://ollama.com"
    ollama_cloud_api_key: SecretStr = SecretStr("")
    ollama_cloud_text_model: str = ""
    openai_compatible_base_url: str = ""
    openai_compatible_api_key: SecretStr = SecretStr("")
    openai_compatible_text_model: str = ""
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_allowed_user_ids: str = ""

    @property
    def allowed_user_ids(self) -> frozenset[int]:
        """Telegram user ids allowed to use the bot. Empty or malformed entries are ignored."""
        ids = (p.strip() for p in self.telegram_allowed_user_ids.split(","))
        return frozenset(int(p) for p in ids if p.lstrip("-").isdigit())


@dataclass
class Vault:
    root: Path
    settings: dict[str, Any] = field(default_factory=dict)
    privacy: dict[str, Any] = field(default_factory=dict)
    provider: ProviderSettings = field(default_factory=ProviderSettings)

    def path(self, key: str) -> Path:
        return self.root / self.settings["paths"][key]


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_vault(root: Path | None = None, provider: ProviderSettings | None = None) -> Vault:
    root = (root or ROOT).resolve()
    return Vault(
        root=root,
        settings=_load_yaml(root / "config" / "settings.yaml"),
        privacy=_load_yaml(root / "config" / "privacy.yaml"),
        provider=provider or ProviderSettings(),
    )
