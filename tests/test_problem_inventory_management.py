from pathlib import Path

import pytest

from gemma_tutor_edge.jobs import build_part5_practice_item, build_seed_ready_pack
from gemma_tutor_edge.storage import SqliteStore


@pytest.mark.asyncio
async def test_problem_inventory_detail_and_delete_roundtrip(tmp_path: Path):
    store = SqliteStore(tmp_path / "problem-management.db")
    await store.init()

    ready_pack = build_seed_ready_pack(topic="Part 5 핵심 문법 10선", mode="toeic", difficulty="easy")
    await store.save_ready_pack("u1", "rp-1", ready_pack, created_at="2026-04-14T00:00:00+00:00")

    practice_item = build_part5_practice_item(0, "easy")
    await store.save_practice_item(
        user_id="u1",
        item=practice_item,
        source="worker_generated",
        created_at="2026-04-14T00:00:00+00:00",
    )

    ready_detail = await store.get_ready_pack("u1", "rp-1")
    assert ready_detail is not None
    assert ready_detail.pack.title == "Part 5 핵심 문법 10선"

    item_detail = await store.get_practice_item("u1", practice_item.item_id)
    assert item_detail is not None
    assert item_detail.item.item_id == practice_item.item_id

    assert await store.delete_ready_pack("u1", "rp-1") is True
    assert await store.delete_practice_item("u1", practice_item.item_id) is True

    assert await store.get_ready_pack("u1", "rp-1") is None
    assert await store.get_practice_item("u1", practice_item.item_id) is None


@pytest.mark.asyncio
async def test_ready_pack_generation_metadata_roundtrip(tmp_path: Path):
    store = SqliteStore(tmp_path / "ready-pack-generation.db")
    await store.init()

    ready_pack = build_seed_ready_pack(topic="Part 5 핵심 문법 10선", mode="toeic", difficulty="easy")
    await store.save_ready_pack(
        "u1",
        "rp-meta",
        ready_pack,
        created_at="2026-04-20T00:00:00+00:00",
        generation_meta={
            "strategy": "llm_invalid_fallback",
            "validated": True,
            "validation_errors": ["item_0_prompt_not_english"],
            "error": None,
            "harness": {"passed": False, "failures": ["item_0_prompt_not_english"], "item_count": 3},
        },
    )

    inventory = await store.problem_inventory("u1")
    assert inventory.ready_packs[0].generation is not None
    assert inventory.ready_packs[0].generation.strategy == "llm_invalid_fallback"
    assert inventory.ready_packs[0].generation.validation_errors == ["item_0_prompt_not_english"]

    ready_detail = await store.get_ready_pack("u1", "rp-meta")
    assert ready_detail is not None
    assert ready_detail.generation is not None
    assert ready_detail.generation.strategy == "llm_invalid_fallback"
    assert ready_detail.generation.harness["passed"] is False
