"""Runtime configuration. Secrets are read from the environment only."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
DEFAULT_FALLBACK_MODEL = "nvidia/Nemotron-3_5-Lightning"
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    nebius_api_key: str = Field(default="", alias="NEBIUS_API_KEY")
    nebius_base_url: str = Field(default=DEFAULT_BASE_URL, alias="NEBIUS_BASE_URL")
    nebius_model: str = Field(default=DEFAULT_MODEL, alias="NEBIUS_MODEL")
    nebius_fallback_model: str = Field(
        default=DEFAULT_FALLBACK_MODEL, alias="NEBIUS_FALLBACK_MODEL"
    )
    audit_ledger_key: str = Field(default="", alias="AUDIT_LEDGER_KEY")
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    meshcfo_ledger_path: str = Field(
        default=".meshcfo/audit.jsonl", alias="MESHCFO_LEDGER_PATH"
    )

    @property
    def live_llm_ready(self) -> bool:
        return bool(self.nebius_api_key.strip())

    @property
    def ledger_path(self) -> Path:
        path = Path(self.meshcfo_ledger_path)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path


def get_settings() -> Settings:
    return Settings()
