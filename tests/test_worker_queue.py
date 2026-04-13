from pathlib import Path

import pytest

from gemma_tutor_edge.jobs import enqueue_prebuild_job, enqueue_problem_generation_job, process_job
from gemma_tutor_edge.schemas import ReadyPackLaunchRequest
from gemma_tutor_edge.services import launch_ready_pack
from gemma_tutor_edge.storage import SqliteStore


@pytest.mark.asyncio
async def test_worker_creates_ready_pack(tmp_path: Path):
    store = SqliteStore(tmp_path / "worker.db")
    await store.init()
    job = await enqueue_prebuild_job(store, user_id="u1", topic="travel English")
    fetched = await store.fetch_next_job()
    assert fetched is not None
    result = await process_job(store=store, model="test", job=fetched)
    assert result["status"] == "prebuilt"
    assert result["generation"]["strategy"] == "seed_fallback"
    assert result["generation"]["validated"] is True
    assert result["item_count"] >= 3
    ready = await store.list_ready_packs("u1")
    assert len(ready) == 1

    launched = await launch_ready_pack(
        store=store,
        ready_pack_id=ready[0].ready_pack_id,
        request=ReadyPackLaunchRequest(user_id="u1"),
    )
    assert launched.ready_pack_id == ready[0].ready_pack_id
    assert launched.quiz_id
    assert len(launched.pack.items) >= 3
    assert all(item.explanation for item in launched.pack.items)


@pytest.mark.asyncio
async def test_worker_generates_problem_set_with_ready_packs_and_practice_items(tmp_path: Path):
    store = SqliteStore(tmp_path / "problem-set.db")
    await store.init()
    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part2": 2, "part5": 3},
    )
    result = await process_job(store=store, model="test", job=job)
    assert result["status"] == "generated"
    assert result["ready_pack_count"] == 5
    assert result["practice_item_count"] == 3

    inventory = await store.problem_inventory("u1")
    assert inventory.stats.total_ready_packs == 5
    assert inventory.stats.total_practice_items == 3
    assert inventory.stats.practice_items_by_part["part5"] == 3
