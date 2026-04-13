from pathlib import Path

import pytest

from gemma_tutor_edge.schemas import ToeicAnswerRequest, ToeicNextRequest
from gemma_tutor_edge.services import get_toeic_next_item, submit_toeic_answer
from gemma_tutor_edge.storage import SqliteStore


@pytest.mark.asyncio
async def test_toeic_next_item_starts_with_medium_seed(tmp_path: Path):
    store = SqliteStore(tmp_path / "toeic.db")
    await store.init()

    response = await get_toeic_next_item(
        store=store,
        request=ToeicNextRequest(user_id="demo-user"),
    )

    assert response.item.part_type == "part5"
    assert response.item.difficulty_level == "medium"
    assert response.recommended_difficulty == "medium"
    assert response.recent_accuracy == 0.0


@pytest.mark.asyncio
async def test_toeic_wrong_answer_updates_weak_tags_and_lowers_difficulty(tmp_path: Path):
    store = SqliteStore(tmp_path / "toeic_answer.db")
    await store.init()

    next_item = await get_toeic_next_item(
        store=store,
        request=ToeicNextRequest(user_id="demo-user"),
    )
    answer = await submit_toeic_answer(
        store=store,
        request=ToeicAnswerRequest(
            user_id="demo-user",
            item_id=next_item.item.item_id,
            selected_option="incorrect",
            response_time_ms=42000,
        ),
    )

    assert answer.correct is False
    assert answer.grammar_tag == next_item.item.grammar_tag
    assert next_item.item.grammar_tag in answer.weak_tags
    assert answer.recommended_difficulty == "easy"

    attempts = await store.list_recent_toeic_attempts("demo-user")
    assert len(attempts) == 1
    assert attempts[0]["response_time_ms"] == 42000
