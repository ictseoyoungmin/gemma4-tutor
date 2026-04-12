from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Gemma Tutor Edge"
    app_env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_db_path: Path = Path("./data/gemma_tutor_edge.db")
    app_storage_dir: Path = Path("./data/storage")

    llm_backend: Literal["google", "llama_cpp", "test"] = "google"

    gemini_api_key: str | None = None
    google_api_key: str | None = None
    google_model: str = "gemini-3-flash-preview"

    llama_base_url: str = "http://127.0.0.1:8080/v1"
    llama_api_key: str = "local-not-required"
    llama_model: str = "gemma-4-e2b-it"
    llama_vision_enabled: bool = True

    enable_logfire: bool = False
    logfire_token: str | None = None

    @property
    def resolved_google_api_key(self) -> str | None:
        return self.gemini_api_key or self.google_api_key

    @model_validator(mode="after")
    def ensure_dirs(self) -> "Settings":
        self.app_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.app_storage_dir.mkdir(parents=True, exist_ok=True)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
