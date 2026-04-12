from __future__ import annotations

from typing import Any

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider

from .config import Settings


def build_model(settings: Settings):
    if settings.llm_backend == "google":
        api_key = settings.resolved_google_api_key
        if not api_key:
            raise RuntimeError(
                "Google backend selected but no GEMINI_API_KEY/GOOGLE_API_KEY was provided."
            )
        provider = GoogleProvider(api_key=api_key)
        return GoogleModel(settings.google_model, provider=provider)

    if settings.llm_backend == "llama_cpp":
        provider = OpenAIProvider(
            base_url=settings.llama_base_url,
            api_key=settings.llama_api_key,
        )
        return OpenAIChatModel(settings.llama_model, provider=provider)

    return "test"
