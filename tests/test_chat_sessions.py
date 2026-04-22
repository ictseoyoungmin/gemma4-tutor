from __future__ import annotations

from pathlib import Path

import pytest
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from gemma_tutor_edge.schemas import ChatRequest, TutorResponse
from gemma_tutor_edge.services import handle_chat
from gemma_tutor_edge.storage import SqliteStore


class _FakeUsage:
    def opentelemetry_attributes(self) -> dict[str, int]:
        return {"input_tokens": 1, "output_tokens": 1}


class _FakeRunResult:
    def __init__(self, *, run_id: str, output: TutorResponse, messages: list[ModelRequest | ModelResponse]):
        self.run_id = run_id
        self.output = output
        self._messages = messages

    def usage(self) -> _FakeUsage:
        return _FakeUsage()

    def all_messages_json(self) -> bytes:
        return ModelMessagesTypeAdapter.dump_json(self._messages)


class _FakeAgent:
    def __init__(self, results: list[_FakeRunResult]):
        self._results = results
        self.calls: list[dict[str, object]] = []

    async def run(self, message: str, *, deps, message_history):
        self.calls.append(
            {
                "message": message,
                "user_id": deps.user_id,
                "message_history": list(message_history),
            }
        )
        return self._results[len(self.calls) - 1]


@pytest.mark.asyncio
async def test_handle_chat_reuses_session_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store = SqliteStore(tmp_path / "test.db")
    await store.init()

    history1 = [
        ModelRequest(parts=[UserPromptPart(content="Hello tutor")]),
        ModelResponse(parts=[TextPart(content="Hi! What do you want to practice today?")]),
    ]
    history2 = [
        *history1,
        ModelRequest(parts=[UserPromptPart(content="Let's continue")]),
        ModelResponse(parts=[TextPart(content="Sure, let's continue from there.")]),
    ]
    fake_agent = _FakeAgent(
        [
            _FakeRunResult(
                run_id="run-1",
                output=TutorResponse(message="Hi! What do you want to practice today?"),
                messages=history1,
            ),
            _FakeRunResult(
                run_id="run-2",
                output=TutorResponse(message="Sure, let's continue from there."),
                messages=history2,
            ),
        ]
    )

    monkeypatch.setattr("gemma_tutor_edge.services.build_tutor_agent", lambda _model: fake_agent)

    first = await handle_chat(
        model="fake-model",
        store=store,
        request=ChatRequest(user_id="u1", message="Hello tutor"),
    )
    second = await handle_chat(
        model="fake-model",
        store=store,
        request=ChatRequest(user_id="u1", session_id=first.session_id, message="Let's continue"),
    )

    assert first.session_id == second.session_id
    assert fake_agent.calls[0]["message_history"] == []
    assert fake_agent.calls[1]["message_history"] == history1
    assert await store.load_chat_history("u1", first.session_id) == history2
