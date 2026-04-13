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
