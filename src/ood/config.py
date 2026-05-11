from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from defaults, .env, environment, and overrides."""

    model_config = SettingsConfigDict(env_prefix="OOD_", env_file=".env", extra="ignore")

    knowledge_dir: Path = Path("knowledge")
    data_dir: Path = Path("data")
    storage_dir: Path | None = None
    eval_dataset_path: Path = Field(
        default=Path("evaluation/datasets/mock-v1.json"),
        validation_alias=AliasChoices("OOD_EVAL_DATASET", "OOD_EVAL_DATASET_PATH", "eval_dataset_path"),
    )
    llm_provider: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    allow_cloud_llm: bool = False
    verbose: int = 0
    quiet: bool = False

    @model_validator(mode="after")
    def derive_storage_dir(self) -> Settings:
        """Default storage below the effective data directory when not configured."""

        if self.storage_dir is None:
            self.storage_dir = self.data_dir / "storage"
        return self

    @property
    def has_llm_credentials(self) -> bool:
        """Return whether a Cloud LLM API key is configured."""

        return self.llm_api_key is not None and bool(self.llm_api_key.get_secret_value())

    @property
    def can_use_cloud_llm(self) -> bool:
        """Return whether content may be sent to a Cloud LLM."""

        return self.allow_cloud_llm and self.has_llm_credentials


def load_settings(**overrides: Any) -> Settings:
    """Load settings with explicit CLI-style overrides taking highest precedence."""

    return Settings(**overrides)


__all__ = ["Settings", "load_settings"]
