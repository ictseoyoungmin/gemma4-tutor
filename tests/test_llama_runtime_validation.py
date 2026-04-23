from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import gemma_tutor_edge.app as app_module
from gemma_tutor_edge.config import Settings
from gemma_tutor_edge.llm import (
    resolve_active_model_name,
    resolve_backend_for_model_name,
    validate_requested_model_name,
)
from gemma_tutor_edge.schemas import ChatRequest, TutorResponse
from gemma_tutor_edge.services import analyze_image, handle_chat
from gemma_tutor_edge.storage import SqliteStore


def test_validate_requested_model_name_allows_local_gguf_from_google_default(tmp_path: Path):
    settings = Settings(
        llm_backend="google",
        gemini_api_key="demo-key",
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    assert validate_requested_model_name(settings, "gemma-4-E2B-it-Q4_K_M.gguf") == "gemma-4-E2B-it-Q4_K_M.gguf"
    assert resolve_backend_for_model_name(settings, "gemma-4-E2B-it-Q4_K_M.gguf") == "llama_cpp"


def test_validate_requested_model_name_rejects_wrong_llama_model(tmp_path: Path):
    settings = Settings(
        llm_backend="llama_cpp",
        llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    with pytest.raises(ValueError, match="does not match the configured llama.cpp served model"):
        validate_requested_model_name(settings, "other-local-model.gguf")


def test_resolve_backend_for_model_name_uses_google_for_non_gguf_model(tmp_path: Path):
    settings = Settings(
        llm_backend="llama_cpp",
        llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
        app_db_path=tmp_path / "test.db",
        app_storage_dir=tmp_path / "storage",
    )

    assert resolve_backend_for_model_name(settings, "gemini-2.5-flash") == "google"


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
async def test_handle_chat_allows_google_model_when_default_backend_is_llama(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    store = SqliteStore(tmp_path / "chat.db")
    await store.init()
    captured: dict[str, object] = {}

    class _FakeGoogleAgent:
        async def run(self, message: str, *, deps, message_history, model_settings=None):
            captured["message"] = message
            captured["user_id"] = deps.user_id
            captured["message_history"] = list(message_history)
            captured["model_settings"] = model_settings

            class _Usage:
                def opentelemetry_attributes(self) -> dict[str, int]:
                    return {"input_tokens": 1, "output_tokens": 1}

            class _Result:
                run_id = "run-google"
                output = TutorResponse(message="google path ok")

                def usage(self):
                    return _Usage()

                def all_messages_json(self) -> bytes:
                    return b"[]"

            return _Result()

    monkeypatch.setattr(
        "gemma_tutor_edge.services.get_settings",
        lambda: Settings(
            llm_backend="llama_cpp",
            llama_model="gemma-4-E2B-it-Q4_K_M.gguf",
            gemini_api_key="demo-key",
            app_db_path=tmp_path / "chat.db",
            app_storage_dir=tmp_path / "storage",
        ),
    )
    monkeypatch.setattr("gemma_tutor_edge.services.build_tutor_agent", lambda _model: _FakeGoogleAgent())

    response = await handle_chat(
        model="fake-model",
        store=store,
        request=ChatRequest(
            user_id="u1",
            message="hello",
            model_name="gemini-2.5-flash",
        ),
    )

    assert response.run_id == "run-google"
    assert captured["message"] == "hello"
    assert captured["model_settings"] is None


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


def test_chat_stream_route_returns_400_for_invalid_model_selection(monkeypatch):
    async def fake_build_chat_stream(*, model, store, request):
        raise ValueError("Requested model mismatch for active backend.")

    monkeypatch.setattr(app_module, "build_chat_stream", fake_build_chat_stream)

    client = TestClient(app_module.app)
    response = client.post(
        "/v1/chat/stream",
        json={
            "user_id": "demo-user",
            "message": "hello",
            "model_name": "gemini-2.5-flash",
        },
    )

    assert response.status_code == 400
    assert "Requested model mismatch" in response.json()["detail"]


def test_chat_stream_route_streams_ndjson(monkeypatch):
    async def fake_build_chat_stream(*, model, store, request):
        async def _stream():
            yield '{"type":"metadata","session_id":"sess-1","backend":"llama_cpp","model_name":"gemma"}\n'
            yield '{"type":"message_delta","delta":"hello"}\n'
            yield '{"type":"final","response":{"session_id":"sess-1","run_id":"run-1","output":{"message":"hello","detected_intent":"chat","memory_to_store":[],"suggested_next_actions":[]},"reasoning":"plan","diagnostics":{"streaming":true},"usage":{}}}\n'

        return _stream()

    monkeypatch.setattr(app_module, "build_chat_stream", fake_build_chat_stream)

    client = TestClient(app_module.app)
    response = client.post(
        "/v1/chat/stream",
        json={
            "user_id": "demo-user",
            "message": "hello",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert '"type":"metadata"' in response.text
    assert '"type":"final"' in response.text


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
