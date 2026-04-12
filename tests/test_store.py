from pathlib import Path

import pytest

from gemma_tutor_edge.schemas import MemoryItem
from gemma_tutor_edge.storage import SqliteStore


@pytest.mark.asyncio
async def test_store_roundtrip(tmp_path: Path):
    db_path = tmp_path / "test.db"
    store = SqliteStore(db_path)
    await store.init()
    item = MemoryItem(category="fact", content="User improved by 10 points.")
    await store.add_memory("u1", item)
    memories = await store.list_recent_memories("u1")
    assert memories
    assert memories[0].content == "User improved by 10 points."
