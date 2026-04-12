from pathlib import Path

import pytest

from gemma_tutor_edge.jobs import enqueue_prebuild_job, process_job
from gemma_tutor_edge.schemas import BackgroundJob
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
    ready = await store.list_ready_packs("u1")
    assert len(ready) == 1
