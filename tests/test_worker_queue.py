from pathlib import Path

import pytest

from gemma_tutor_edge.jobs import enqueue_prebuild_job, process_job
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
