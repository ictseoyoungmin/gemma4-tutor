from pathlib import Path

import pytest

from gemma_tutor_edge.storage import SqliteStore


@pytest.mark.asyncio
async def test_dashboard_detail_contains_placeholders(tmp_path: Path):
    store = SqliteStore(tmp_path / "detail.db")
    await store.init()
    detail = await store.dashboard_detail("demo-user")
    assert detail.overview.user_id == "demo-user"
    assert len(detail.skill_snapshots) >= 1
    assert len(detail.achievements) >= 1
    assert len(detail.roadmap_placeholders) >= 1
