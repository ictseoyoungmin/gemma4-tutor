from __future__ import annotations

import pytest

import gemma_tutor_edge.app as app_module
from gemma_tutor_edge.harness.runner import execute_harness, validate_generated_pack
from gemma_tutor_edge.jobs import build_seed_ready_pack


@pytest.mark.asyncio
async def test_execute_harness_passes_with_test_backend(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app_module, "model", "test")
    result = await execute_harness(mode="asgi")
    assert result.total >= 2
    assert result.passed == result.total


def test_validate_generated_pack_accepts_english_items_and_korean_explanations():
    pack = build_seed_ready_pack(topic="Part 5 핵심 문법 10선", mode="toeic", difficulty="easy")
    result = validate_generated_pack(pack)
    assert result["passed"] is True
    assert result["item_count"] >= 3
