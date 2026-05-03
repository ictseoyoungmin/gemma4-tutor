from __future__ import annotations

from fastapi.testclient import TestClient

import gemma_tutor_edge.app as app_module


def test_image_analyze_accepts_model_name_and_file(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_analyze_image(*, model, store, user_id, prompt, image_bytes, media_type, model_name=None):
        captured["model"] = model
        captured["store"] = store
        captured["user_id"] = user_id
        captured["prompt"] = prompt
        captured["image_bytes"] = image_bytes
        captured["media_type"] = media_type
        captured["model_name"] = model_name
        return {
            "scene_summary": "A learner is reviewing a page.",
            "vocabulary": ["page", "desk"],
            "suggested_question_types": ["Describe the scene"],
            "generated_prompt_seed": "Describe what the learner is doing.",
        }

    monkeypatch.setattr(app_module, "analyze_image", fake_analyze_image)

    client = TestClient(app_module.app)
    response = client.post(
        "/v1/image/analyze",
        data={
            "user_id": "demo-user",
            "prompt": "Turn this into a short English lesson.",
            "model_name": "gemini-2.5-flash",
        },
        files={"file": ("desk.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["scene_summary"] == "A learner is reviewing a page."
    assert captured["user_id"] == "demo-user"
    assert captured["prompt"] == "Turn this into a short English lesson."
    assert captured["image_bytes"] == b"fake-image-bytes"
    assert captured["media_type"] == "image/png"
    assert captured["model_name"] == "gemini-2.5-flash"
