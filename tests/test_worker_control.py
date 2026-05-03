from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from gemma_tutor_edge.jobs import enqueue_prebuild_job
from gemma_tutor_edge.storage import SqliteStore
from gemma_tutor_edge.worker_control import WorkerController


@pytest.mark.asyncio
async def test_worker_controller_processes_job_and_handles_stop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "worker-control.db"
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    monkeypatch.setenv("APP_DB_PATH", str(db_path))
    monkeypatch.setenv("APP_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("LLM_BACKEND", "test")

    store = SqliteStore(db_path)
    await store.init()
    await enqueue_prebuild_job(store, user_id="u1", topic="worker integration", mode="toeic", difficulty="medium")

    controller = WorkerController(project_root=Path(__file__).resolve().parents[1])
    started = controller.start(poll_interval=0.1, max_jobs=1)
    assert started.state == "running"
    assert started.pid is not None

    for _ in range(50):
        ready = await store.list_ready_packs("u1")
        status = controller.status()
        if ready and status.state == "stopped":
            break
        await asyncio.sleep(0.1)

    ready = await store.list_ready_packs("u1")
    status = controller.status()
    assert len(ready) == 1
    assert status.state == "stopped"
    assert status.last_exit_code == 0

    stopped_again = controller.stop()
    assert stopped_again.state == "stopped"
    assert stopped_again.last_exit_code == 0
