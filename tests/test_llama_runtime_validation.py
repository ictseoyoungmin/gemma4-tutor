from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import gemma_tutor_edge.app as app_module
from gemma_tutor_edge.config import Settings
from gemma_tutor_edge.llm import resolve_active_model_name, validate_requested_model_name
from gemma_tutor_edge.schemas import ChatRequest
from gemma_tutor_edge.services import analyze_image, handle_chat
from gemma_tutor_edge.storage import SqliteStore


def test_validate_requested_model_name_rejects_gguf_on_google_backend(tmp_path: Path):
    settings = Settings(
        llm_backend="google",
        gemini_api_key="demo-key",
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    with pytest.raises(ValueError, match="active backend is 'google'"):
        validate_requested_model_name(settings, "gemma-4-E2B-it-Q4_K_M.gguf")


def test_validate_requested_model_name_rejects_wrong_llama_model(tmp_path: Path):
    settings = Settings(
        llm_backend="llama_cpp",
        llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    with pytest.raises(ValueError, match="does not match the active llama.cpp served model"):
        validate_requested_model_name(settings, "gemini-2.5-flash")


def test_resolve_active_model_name_uses_backend_specific_default(tmp_path: Path):
    google_settings = Settings(
        llm_backend="google",
        google_model="gemini-2.5-flash",
        gemini_api_key="demo-key",
        app_db_path=tmp_path / "google.db",
        app_storage_dir=tmp_path / "google-storage",
    )
    llama_settings = Settings(
        llm_backend="llama_cpp",
        llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
        app_db_path=tmp_path / "llama.db",
        app_storage_dir=tmp_path / "llama-storage",
    )

    assert resolve_active_model_name(google_settings) == "gemini-2.5-flash"
    assert resolve_active_model_name(llama_settings) == "gemma-4-E2B-it-Q4_K_M.gguf"


@pytest.mark.asyncio
async def test_handle_chat_rejects_mismatched_model_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store = SqliteStore(tmp_path / "chat.db")
    await store.init()
    monkeypatch.setattr(
        "gemma_tutor_edge.services.get_settings",
        lambda: Settings(
            llm_backend="llama_cpp",
            llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
            app_db_path=tmp_path / "chat.db",
            app_storage_dir=tmp_path / "storage",
        ),
    )

    with pytest.raises(ValueError, match="active llama.cpp served model"):
        await handle_chat(
            model="fake-model",
            store=store,
            request=ChatRequest(
                user_id="u1",
                message="hello",
                model_name="gemini-2.5-flash",
            ),
        )


@pytest.mark.asyncio
async def test_analyze_image_rejects_when_llama_vision_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    store = SqliteStore(tmp_path / "vision.db")
    await store.init()
    monkeypatch.setattr(
        "gemma_tutor_edge.services.get_settings",
        lambda: Settings(
            llm_backend="llama_cpp",
            llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
            llama_vision_enabled=False,
            app_db_path=tmp_path / "vision.db",
            app_storage_dir=tmp_path / "storage",
        ),
    )

    with pytest.raises(ValueError, match="LLAMA_VISION_ENABLED=false"):
        await analyze_image(
            model="fake-model",
            store=store,
            user_id="u1",
            prompt="describe",
            image_bytes=b"fake-image",
            media_type="image/png",
            model_name="gemma-4-E2B-it-Q4_K_M.gguf",
        )


def test_chat_route_returns_400_for_invalid_model_selection(monkeypatch):
    async def fake_handle_chat(*, model, store, request):
        raise ValueError("Requested model mismatch for active backend.")

    monkeypatch.setattr(app_module, "handle_chat", fake_handle_chat)

    client = TestClient(app_module.app)
    response = client.post(
        "/v1/chat",
        json={
            "user_id": "demo-user",
            "message": "hello",
            "model_name": "gemini-2.5-flash",
        },
    )

    assert response.status_code == 400
    assert "Requested model mismatch" in response.json()["detail"]


def test_image_route_returns_400_for_disabled_llama_vision(monkeypatch):
    async def fake_analyze_image(*, model, store, user_id, prompt, image_bytes, media_type, model_name=None):
        raise ValueError("Image analysis is disabled for the active llama.cpp backend because LLAMA_VISION_ENABLED=false.")

    monkeypatch.setattr(app_module, "analyze_image", fake_analyze_image)

    client = TestClient(app_module.app)
    response = client.post(
        "/v1/image/analyze",
        data={
            "user_id": "demo-user",
            "prompt": "describe this image",
            "model_name": "gemma-4-E2B-it-Q4_K_M.gguf",
        },
        files={"file": ("tiny.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 400
    assert "LLAMA_VISION_ENABLED=false" in response.json()["detail"]
