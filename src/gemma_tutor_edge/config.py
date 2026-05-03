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
    llama_model: str = "gemma-4-E2B-it-Q4_K_M.gguf"
    llama_vision_enabled: bool = True
    llama_chat_thinking_enabled: bool = False
    llama_chat_max_tokens: int = 8400
    llama_chat_temperature: float | None = None
    model_dir: Path = Field(default_factory=lambda: Path.home() / "models")
    llama_gguf_path: Path | None = None
    llama_mmproj_path: Path | None = None
    validate_llama_assets: bool = False

    enable_logfire: bool = False
    logfire_token: str | None = None

    @property
    def resolved_google_api_key(self) -> str | None:
        return self.gemini_api_key or self.google_api_key

    @property
    def resolved_model_dir(self) -> Path:
        return self.model_dir.expanduser()

    @property
    def resolved_llama_gguf_path(self) -> Path:
        if self.llama_gguf_path is not None:
            return self.llama_gguf_path.expanduser()
        return self.resolved_model_dir / "gemma-4-E2B-it-Q4_K_M.gguf"

    @property
    def resolved_llama_mmproj_path(self) -> Path:
        if self.llama_mmproj_path is not None:
            return self.llama_mmproj_path.expanduser()
        return self.resolved_model_dir / "mmproj-F16.gguf"

    @model_validator(mode="after")
    def ensure_dirs(self) -> "Settings":
        self.app_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.app_storage_dir.mkdir(parents=True, exist_ok=True)
        if self.llm_backend == "llama_cpp" and self.validate_llama_assets:
            missing = []
            if not self.resolved_llama_gguf_path.is_file():
                missing.append(f"GGUF model file not found: {self.resolved_llama_gguf_path}")
            if not self.resolved_llama_mmproj_path.is_file():
                missing.append(
                    f"Multimodal projector file not found: {self.resolved_llama_mmproj_path}"
                )
            if missing:
                joined = " | ".join(missing)
                raise ValueError(
                    "Local llama.cpp asset validation failed. "
                    f"{joined}. Update MODEL_DIR / LLAMA_GGUF_PATH / LLAMA_MMPROJ_PATH "
                    "or disable VALIDATE_LLAMA_ASSETS for externally managed runtimes."
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
