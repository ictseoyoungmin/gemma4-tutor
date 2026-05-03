from __future__ import annotations

from typing import Any

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings


def resolve_active_model_name(settings: Settings) -> str:
    if settings.llm_backend == "google":
        return settings.google_model
    if settings.llm_backend == "llama_cpp":
        return settings.llama_model
    return "test"


def resolve_backend_for_model_name(
    settings: Settings, model_name: str | None
) -> str:
    if not model_name or not model_name.strip():
        return settings.llm_backend

    requested = model_name.strip()
    if requested.endswith(".gguf"):
        return "llama_cpp"
    return "google"


def validate_requested_model_name(settings: Settings, model_name: str | None) -> str | None:
    if not model_name:
        return None

    requested = model_name.strip()
    if not requested:
        return None

    requested_backend = resolve_backend_for_model_name(settings, requested)

    if requested_backend == "google":
        return requested

    if requested_backend == "llama_cpp":
        active_model = settings.llama_model
        if requested != active_model:
            raise ValueError(
                f"Requested local model '{requested}' does not match the configured llama.cpp served model "
                f"'{active_model}'. Update LLAMA_MODEL or choose the configured local model."
            )
        return requested

    return requested


def build_model_for_name(settings: Settings, model_name: str | None):
    validated_model_name = validate_requested_model_name(settings, model_name)
    selected_backend = resolve_backend_for_model_name(settings, validated_model_name)

    if selected_backend == "google":
        api_key = settings.resolved_google_api_key
        if not api_key:
            raise RuntimeError(
                "Google backend selected but no GEMINI_API_KEY/GOOGLE_API_KEY was provided."
            )
        provider = GoogleProvider(api_key=api_key)
        return GoogleModel(validated_model_name or settings.google_model, provider=provider)

    if selected_backend == "llama_cpp":
        provider = OpenAIProvider(
            base_url=settings.llama_base_url,
            api_key=settings.llama_api_key,
        )
        return OpenAIChatModel(validated_model_name or settings.llama_model, provider=provider)

    return "test"


def build_model(settings: Settings):
    return build_model_for_name(settings, None)
