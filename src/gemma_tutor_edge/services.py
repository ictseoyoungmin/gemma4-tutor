from __future__ import annotations

import json
from time import perf_counter
from uuid import uuid4

import httpx

from .agents import (
    LOCAL_TUTOR_SYSTEM_PROMPT,
    build_local_tutor_agent,
    build_quiz_agent,
    build_tutor_agent,
    build_vision_agent,
    run_image_analysis,
)
from .config import get_settings
from .deps import ContentDeps, TutorDeps
from .jobs import build_seed_ready_pack, enqueue_prebuild_job
from .jobs import enqueue_problem_generation_job
from .llm import build_model_for_name, resolve_backend_for_model_name
from .schemas import (
    ChatRequest,
    TutorResponse,
    ChatResponse,
    DeleteResourceResponse,
    ImageAnalysisResponse,
    ProblemGenerationRequest,
    ProblemGenerationResponse,
    ProblemInventoryResponse,
    PracticeItemDetail,
    QueueJobRequest,
    QueueJobResponse,
    ReadyPackLaunchRequest,
    ReadyPackDetail,
    ReadyPackLaunchResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    ToeicAnswerRequest,
    ToeicAnswerResponse,
    ToeicNextRequest,
    ToeicNextResponse,
)
from .storage import SqliteStore
from .toeic import TOEIC_ITEMS, get_item_by_id, select_next_item

UI_JSON_START = "<ui_json>"
UI_JSON_END = "</ui_json>"


async def _resolve_chat_session(
    *,
    store: SqliteStore,
    user_id: str,
    requested_session_id: str | None,
    backend: str,
    model_name: str,
    load_history: bool = True,
) -> tuple[str, list, dict[str, object]]:
    session_id = requested_session_id or uuid4().hex
    diagnostics: dict[str, object] = {}
    if not requested_session_id:
        return session_id, [], diagnostics

    session_meta = await store.get_chat_session_meta(user_id, requested_session_id)
    if session_meta is None:
        return session_id, [], diagnostics

    backend_changed = session_meta.backend not in (None, backend)
    model_changed = session_meta.model_name not in (None, model_name)
    if backend_changed or model_changed:
        new_session_id = uuid4().hex
        diagnostics.update(
            {
                "session_reset": True,
                "replaced_session_id": requested_session_id,
                "session_reset_reason": (
                    "backend_changed" if backend_changed else "model_changed"
                ),
            }
        )
        return new_session_id, [], diagnostics

    if not load_history:
        return requested_session_id, [], diagnostics

    return requested_session_id, await store.load_chat_history(user_id, requested_session_id), diagnostics


async def handle_chat(*, model, store: SqliteStore, request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    selected_model = build_model_for_name(settings, request.model_name) if request.model_name else model
    selected_backend = resolve_backend_for_model_name(settings, request.model_name)
    active_model_name = request.model_name or (
        settings.llama_model if selected_backend == "llama_cpp" else settings.google_model
    )
    session_id, message_history, session_diagnostics = await _resolve_chat_session(
        store=store,
        user_id=request.user_id,
        requested_session_id=request.session_id,
        backend=selected_backend,
        model_name=active_model_name,
        load_history=selected_backend != "llama_cpp",
    )
    started_at = perf_counter()
    if selected_model == "test":
        return ChatResponse(
            session_id=session_id,
            run_id=f"test-{uuid4().hex[:8]}",
            output={
                "message": "테스트 튜터 응답입니다. 다음 학습으로 짧은 TOEIC 문제를 풀어보세요.",
                "detected_intent": "chat",
                "memory_to_store": [],
                "suggested_next_actions": ["Part 5 문제 풀기", "Ready Pack 확인"],
            },
            diagnostics={
                "backend": "test",
                "model_name": "test",
                "history_messages": 0,
                "streaming": False,
                "total_elapsed_ms": 0,
                **session_diagnostics,
            },
            usage={},
        )
    agent = build_local_tutor_agent(selected_model) if selected_backend == "llama_cpp" else build_tutor_agent(selected_model)
    deps = TutorDeps(user_id=request.user_id, store=store)
    result = await agent.run(
        request.message,
        deps=deps,
        message_history=message_history,
        model_settings=_build_chat_model_settings(
            settings,
            selected_backend,
            reasoning_enabled=request.reasoning_enabled,
        ),
    )
    await store.save_chat_history(
        request.user_id,
        session_id,
        result.all_messages_json(),
        backend=selected_backend,
        model_name=active_model_name,
    )
    output = _normalize_tutor_output(result.output)
    for item in output.memory_to_store:
        await store.add_memory(request.user_id, item)
    elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
    response_message = getattr(result, "response", None)
    return ChatResponse(
        session_id=session_id,
        run_id=result.run_id,
        output=output,
        reasoning=getattr(response_message, "thinking", None),
        diagnostics={
            "backend": selected_backend,
            "model_name": getattr(response_message, "model_name", None) or active_model_name,
            "history_messages": len(message_history),
            "streaming": False,
            "reasoning_enabled": request.reasoning_enabled,
            "total_elapsed_ms": elapsed_ms,
            **session_diagnostics,
        },
        usage=result.usage().opentelemetry_attributes(),
    )


def _build_chat_model_settings(
    settings,
    selected_backend: str,
    *,
    reasoning_enabled: bool | None = None,
) -> dict[str, object] | None:
    if selected_backend != "llama_cpp":
        return None
    effective_reasoning_enabled = (
        settings.llama_chat_thinking_enabled
        if reasoning_enabled is None
        else reasoning_enabled
    )
    model_settings: dict[str, object] = {
        "max_tokens": settings.llama_chat_max_tokens,
    }
    if settings.llama_chat_temperature is not None:
        model_settings["temperature"] = settings.llama_chat_temperature
    if effective_reasoning_enabled:
        model_settings["thinking"] = True
        model_settings["extra_body"] = {
            "reasoning_format": "auto",
        }
    else:
        model_settings["thinking"] = False
    return model_settings


async def build_chat_stream(*, model, store: SqliteStore, request: ChatRequest):
    settings = get_settings()
    selected_model = build_model_for_name(settings, request.model_name) if request.model_name else model
    selected_backend = resolve_backend_for_model_name(settings, request.model_name)
    active_model_name = request.model_name or (
        settings.llama_model if selected_backend == "llama_cpp" else settings.google_model
    )
    session_id, message_history, session_diagnostics = await _resolve_chat_session(
        store=store,
        user_id=request.user_id,
        requested_session_id=request.session_id,
        backend=selected_backend,
        model_name=active_model_name,
        load_history=selected_backend != "llama_cpp",
    )

    if selected_model == "test":
        async def test_stream():
            yield _ndjson(
                {
                    "type": "metadata",
                    "session_id": session_id,
                    "backend": "test",
                    "model_name": "test",
                }
            )
            yield _ndjson({"type": "message_delta", "delta": "테스트 튜터 응답입니다. 다음 학습으로 짧은 TOEIC 문제를 풀어보세요."})
            yield _ndjson(
                {
                    "type": "final",
                    "response": ChatResponse(
                        session_id=session_id,
                        run_id=f"test-{uuid4().hex[:8]}",
                        output={
                            "message": "테스트 튜터 응답입니다. 다음 학습으로 짧은 TOEIC 문제를 풀어보세요.",
                            "detected_intent": "chat",
                            "memory_to_store": [],
                            "suggested_next_actions": ["Part 5 문제 풀기", "Ready Pack 확인"],
                        },
                        diagnostics={
                            "backend": "test",
                            "model_name": "test",
                            "history_messages": 0,
                            "streaming": True,
                            "reasoning_enabled": request.reasoning_enabled,
                            "first_chunk_ms": 0,
                            "total_elapsed_ms": 0,
                            **session_diagnostics,
                        },
                        usage={},
                    ).model_dump(mode="json"),
                }
            )

        return test_stream()

    if selected_backend == "llama_cpp":
        return _build_raw_llama_chat_stream(
            settings=settings,
            store=store,
            request=request,
            session_id=session_id,
            active_model_name=active_model_name,
            session_diagnostics=session_diagnostics,
        )

    agent = build_local_tutor_agent(selected_model) if selected_backend == "llama_cpp" else build_tutor_agent(selected_model)
    deps = TutorDeps(user_id=request.user_id, store=store)
    model_settings = _build_chat_model_settings(
        settings,
        selected_backend,
        reasoning_enabled=request.reasoning_enabled,
    )

    async def event_stream():
        started_at = perf_counter()
        first_chunk_ms: float | None = None
        previous_message = ""
        previous_reasoning = ""

        yield _ndjson(
            {
                "type": "metadata",
                "session_id": session_id,
                "backend": selected_backend,
                "model_name": active_model_name,
            }
        )

        try:
            async with agent.run_stream(
                request.message,
                deps=deps,
                message_history=message_history,
                model_settings=model_settings,
            ) as result:
                async for partial_output in result.stream_output(debounce_by=None):
                    if isinstance(partial_output, str):
                        current_message = partial_output
                    else:
                        current_message = partial_output.message or ""
                    response_message = result.response
                    current_reasoning = getattr(response_message, "thinking", None) or ""

                    if first_chunk_ms is None and (current_message or current_reasoning):
                        first_chunk_ms = round((perf_counter() - started_at) * 1000, 1)
                        yield _ndjson({"type": "metrics", "first_chunk_ms": first_chunk_ms})

                    if current_reasoning != previous_reasoning:
                        reasoning_delta = (
                            current_reasoning[len(previous_reasoning):]
                            if current_reasoning.startswith(previous_reasoning)
                            else current_reasoning
                        )
                        if reasoning_delta:
                            yield _ndjson({"type": "reasoning_delta", "delta": reasoning_delta})
                        previous_reasoning = current_reasoning

                    if current_message != previous_message:
                        message_delta = (
                            current_message[len(previous_message):]
                            if current_message.startswith(previous_message)
                            else current_message
                        )
                        if message_delta:
                            yield _ndjson({"type": "message_delta", "delta": message_delta})
                        previous_message = current_message

                output = _normalize_tutor_output(await result.get_output())
                await store.save_chat_history(
                    request.user_id,
                    session_id,
                    result.all_messages_json(),
                    backend=selected_backend,
                    model_name=active_model_name,
                )
                for item in output.memory_to_store:
                    await store.add_memory(request.user_id, item)

                total_elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
                response_message = result.response
                final_response = ChatResponse(
                    session_id=session_id,
                    run_id=result.run_id,
                    output=output,
                    reasoning=getattr(response_message, "thinking", None),
                    diagnostics={
                        "backend": selected_backend,
                        "model_name": getattr(response_message, "model_name", None) or active_model_name,
                        "history_messages": len(message_history),
                        "streaming": True,
                        "reasoning_enabled": request.reasoning_enabled,
                        "first_chunk_ms": first_chunk_ms,
                        "total_elapsed_ms": total_elapsed_ms,
                        **session_diagnostics,
                    },
                    usage=result.usage().opentelemetry_attributes(),
                )
                yield _ndjson({"type": "final", "response": final_response.model_dump(mode="json")})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": str(exc)})

    return event_stream()


def _build_raw_llama_system_prompt(memories: list) -> str:
    memory_lines = [
        f"- {memory.category}: {memory.content}"
        for memory in memories
        if getattr(memory, "content", "").strip()
    ]
    memory_block = (
        "\n\nRecent learner memory:\n" + "\n".join(memory_lines)
        if memory_lines
        else ""
    )
    routing_block = (
        "\n\nAvailable tutor routes: chat, quiz_request, analysis, memory_update, image_learning. "
        "If the learner asks for a next action, answer naturally and keep any button-like suggestion short."
        "\n\nFor local UI metadata, finish every answer with a hidden block exactly like this:"
        "\n<ui_json>"
        '\n{"detected_intent":"chat","suggested_next_actions":["짧은 다음 행동 1","짧은 다음 행동 2"],"memory_to_store":[]}'
        "\n</ui_json>"
        "\nThe learner-facing answer must come before <ui_json>. "
        "Do not mention <ui_json> in the learner-facing answer. "
        "suggested_next_actions should be natural Korean button labels that fit the current answer."
    )
    return f"{LOCAL_TUTOR_SYSTEM_PROMPT}{memory_block}{routing_block}"


def _build_raw_llama_payload(
    settings,
    request: ChatRequest,
    active_model_name: str,
    *,
    raw_history: list[dict[str, str]],
    memories: list,
) -> dict[str, object]:
    effective_reasoning_enabled = (
        settings.llama_chat_thinking_enabled
        if request.reasoning_enabled is None
        else request.reasoning_enabled
    )
    payload: dict[str, object] = {
        "model": active_model_name,
        "messages": [
            {"role": "system", "content": _build_raw_llama_system_prompt(memories)},
            *raw_history,
            {"role": "user", "content": request.message},
        ],
        "stream": True,
        "max_tokens": settings.llama_chat_max_tokens,
    }
    if settings.llama_chat_temperature is not None:
        payload["temperature"] = settings.llama_chat_temperature
    if effective_reasoning_enabled:
        payload["thinking"] = True
        payload["reasoning_format"] = "auto"
        payload["chat_template_kwargs"] = {"enable_thinking": True}
    else:
        payload["thinking"] = False
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    return payload


def _strip_reasoning_markers(text: str) -> str:
    stripped = text.strip()
    for marker in ("Thinking Process:", "Reasoning:", "Here's a thinking process"):
        index = stripped.lower().find(marker.lower())
        if index >= 0:
            stripped = stripped[:index].strip()
    return stripped


def _longest_suffix_matching_prefix(text: str, marker: str) -> int:
    max_size = min(len(marker) - 1, len(text))
    for size in range(max_size, 0, -1):
        if marker.startswith(text[-size:]):
            return size
    return 0


def _consume_raw_message_delta(delta: str, state: dict[str, object]) -> list[str]:
    visible_parts: list[str] = []
    text = f"{state.get('pending', '')}{delta}"
    state["pending"] = ""

    while text:
        if state.get("in_ui_json"):
            end_index = text.find(UI_JSON_END)
            if end_index >= 0:
                cast_parts = state["ui_json_parts"]
                assert isinstance(cast_parts, list)
                cast_parts.append(text[:end_index])
                text = text[end_index + len(UI_JSON_END):]
                state["in_ui_json"] = False
                continue

            keep = _longest_suffix_matching_prefix(text, UI_JSON_END)
            cast_parts = state["ui_json_parts"]
            assert isinstance(cast_parts, list)
            cast_parts.append(text[:-keep] if keep else text)
            state["pending"] = text[-keep:] if keep else ""
            break

        start_index = text.find(UI_JSON_START)
        if start_index >= 0:
            visible = text[:start_index]
            if visible:
                visible_parts.append(visible)
            text = text[start_index + len(UI_JSON_START):]
            state["in_ui_json"] = True
            continue

        keep = _longest_suffix_matching_prefix(text, UI_JSON_START)
        visible = text[:-keep] if keep else text
        if visible:
            visible_parts.append(visible)
        state["pending"] = text[-keep:] if keep else ""
        break

    return visible_parts


def _flush_raw_message_state(state: dict[str, object]) -> list[str]:
    pending = state.get("pending", "")
    state["pending"] = ""
    if not isinstance(pending, str) or not pending:
        return []
    if state.get("in_ui_json"):
        cast_parts = state["ui_json_parts"]
        assert isinstance(cast_parts, list)
        cast_parts.append(pending)
        return []
    return [pending]


def _parse_ui_json_block(ui_json_text: str) -> dict[str, object]:
    stripped = ui_json_text.strip()
    if not stripped:
        return {}
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        return {}
    try:
        parsed = json.loads(stripped[start:end + 1])
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_raw_tutor_response(raw_message: str, ui_json_text: str) -> TutorResponse:
    message = _strip_reasoning_markers(raw_message)
    metadata = _parse_ui_json_block(ui_json_text)
    payload = {
        "message": message or "응답을 생성하지 못했어요. 한 번 더 짧게 요청해 주세요.",
        "detected_intent": metadata.get("detected_intent", "chat"),
        "memory_to_store": metadata.get("memory_to_store", []),
        "suggested_next_actions": metadata.get("suggested_next_actions", []),
    }
    try:
        return TutorResponse.model_validate(payload)
    except Exception:  # noqa: BLE001
        return TutorResponse(
            message=payload["message"],
            detected_intent="chat",
            memory_to_store=[],
            suggested_next_actions=[],
        )


def _build_raw_llama_chat_stream(
    *,
    settings,
    store: SqliteStore,
    request: ChatRequest,
    session_id: str,
    active_model_name: str,
    session_diagnostics: dict[str, object],
):
    async def event_stream():
        started_at = perf_counter()
        first_chunk_ms: float | None = None
        message_parts: list[str] = []
        reasoning_parts: list[str] = []
        message_state: dict[str, object] = {
            "pending": "",
            "in_ui_json": False,
            "ui_json_parts": [],
        }
        raw_history = (
            await store.load_raw_chat_messages(request.user_id, session_id)
            if request.session_id
            else []
        )
        memories = await store.list_recent_memories(request.user_id, limit=5)

        yield _ndjson(
            {
                "type": "metadata",
                "session_id": session_id,
                "backend": "llama_cpp",
                "model_name": active_model_name,
                "stream_mode": "raw_llama_cpp",
            }
        )

        try:
            url = f"{settings.llama_base_url.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {settings.llama_api_key}"}
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=_build_raw_llama_payload(
                        settings,
                        request,
                        active_model_name,
                        raw_history=raw_history,
                        memories=memories,
                    ),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if not data or data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        choices = chunk.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        reasoning_delta = (
                            delta.get("reasoning_content")
                            or delta.get("reasoning")
                            or delta.get("thinking")
                            or ""
                        )
                        message_delta = delta.get("content") or ""

                        if first_chunk_ms is None and (reasoning_delta or message_delta):
                            first_chunk_ms = round((perf_counter() - started_at) * 1000, 1)
                            yield _ndjson({"type": "metrics", "first_chunk_ms": first_chunk_ms})

                        if reasoning_delta:
                            reasoning_parts.append(reasoning_delta)
                            yield _ndjson({"type": "reasoning_delta", "delta": reasoning_delta})
                        if message_delta:
                            for visible_delta in _consume_raw_message_delta(
                                message_delta,
                                message_state,
                            ):
                                message_parts.append(visible_delta)
                                yield _ndjson({"type": "message_delta", "delta": visible_delta})

            total_elapsed_ms = round((perf_counter() - started_at) * 1000, 1)
            for visible_delta in _flush_raw_message_state(message_state):
                message_parts.append(visible_delta)
                yield _ndjson({"type": "message_delta", "delta": visible_delta})
            ui_json_parts = message_state["ui_json_parts"]
            assert isinstance(ui_json_parts, list)
            message = "".join(message_parts)
            ui_json_text = "".join(str(part) for part in ui_json_parts)
            reasoning = "".join(reasoning_parts).strip() or None
            output = _build_raw_tutor_response(message, ui_json_text)
            next_history = [
                *raw_history,
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": output.message},
            ][-8:]
            await store.save_raw_chat_messages(
                request.user_id,
                session_id,
                next_history,
                backend="llama_cpp",
                model_name=active_model_name,
            )
            final_response = ChatResponse(
                session_id=session_id,
                run_id=f"llama-raw-{uuid4().hex[:8]}",
                output=output,
                reasoning=reasoning,
                diagnostics={
                    "backend": "llama_cpp",
                    "model_name": active_model_name,
                    "history_messages": len(raw_history),
                    "memory_items": len(memories),
                    "streaming": True,
                    "stream_mode": "raw_llama_cpp",
                    "reasoning_enabled": request.reasoning_enabled,
                    "first_chunk_ms": first_chunk_ms,
                    "total_elapsed_ms": total_elapsed_ms,
                    **session_diagnostics,
                },
                usage={},
            )
            yield _ndjson({"type": "final", "response": final_response.model_dump(mode="json")})
        except Exception as exc:  # noqa: BLE001
            yield _ndjson({"type": "error", "message": str(exc)})

    return event_stream()


def _ndjson(payload: dict[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def _normalize_tutor_output(output: TutorResponse | str) -> TutorResponse:
    if isinstance(output, TutorResponse):
        return output
    return TutorResponse(
        message=output.strip(),
        detected_intent="chat",
        memory_to_store=[],
        suggested_next_actions=[],
    )


async def generate_quiz(*, model, store: SqliteStore, request: QuizGenerateRequest) -> QuizGenerateResponse:
    if model == "test":
        quiz_id = uuid4().hex
        pack = build_seed_ready_pack(
            topic=request.topic,
            mode=request.mode,
            difficulty=request.difficulty,
        )
        await store.save_quiz_pack(request.user_id, quiz_id, pack)
        return QuizGenerateResponse(quiz_id=quiz_id, pack=pack)
    agent = build_quiz_agent(model)
    deps = ContentDeps(user_id=request.user_id, store=store)
    prompt = (
        f"Create a {request.mode} quiz pack about: {request.topic}. "
        f"Difficulty: {request.difficulty}. Count: {request.count}."
    )
    result = await agent.run(prompt, deps=deps)
    quiz_id = uuid4().hex
    await store.save_quiz_pack(request.user_id, quiz_id, result.output)
    return QuizGenerateResponse(quiz_id=quiz_id, pack=result.output)


async def submit_quiz(*, store: SqliteStore, request: QuizSubmitRequest) -> QuizSubmitResponse:
    pack = await store.get_quiz_pack(request.quiz_id)
    if pack is None:
        raise ValueError(f"Quiz {request.quiz_id} was not found")
    total = len(pack.items)
    answers = request.answers[:total]
    feedback = []
    correct = 0
    for idx, item in enumerate(pack.items):
        answer = answers[idx] if idx < len(answers) else ""
        is_correct = answer.strip().lower() == item.answer.strip().lower()
        if is_correct:
            correct += 1
            feedback.append(f"Q{idx+1}: correct")
        else:
            feedback.append(
                f"Q{idx+1}: incorrect. Expected '{item.answer}'. {item.explanation}"
            )
    score = correct / total if total else 0.0
    await store.save_attempt(request.user_id, request.quiz_id, total, correct, score, feedback)
    return QuizSubmitResponse(
        quiz_id=request.quiz_id,
        total=total,
        correct=correct,
        feedback=feedback,
        score=score,
    )


async def get_toeic_next_item(*, store: SqliteStore, request: ToeicNextRequest) -> ToeicNextResponse:
    attempts = await store.list_recent_toeic_attempts(request.user_id, limit=10)
    practice_items = await store.list_practice_items(request.user_id, part_type=request.part_type, limit=100)
    item, recommended_difficulty, weak_tags, recent_accuracy = select_next_item(
        attempts=attempts,
        part_type=request.part_type,
        items=practice_items or TOEIC_ITEMS,
    )
    return ToeicNextResponse(
        item=item,
        recommended_difficulty=recommended_difficulty,
        weak_tags=weak_tags,
        recent_accuracy=recent_accuracy,
    )


async def submit_toeic_answer(*, store: SqliteStore, request: ToeicAnswerRequest) -> ToeicAnswerResponse:
    practice_items = await store.list_practice_items(request.user_id, limit=200)
    item = get_item_by_id(request.item_id, practice_items or TOEIC_ITEMS)
    if item is None:
        raise ValueError(f"TOEIC item {request.item_id} was not found")

    correct = request.selected_option.strip().lower() == item.correct_option.strip().lower()
    await store.save_toeic_attempt(
        user_id=request.user_id,
        item=item,
        selected_option=request.selected_option,
        correct=correct,
        response_time_ms=request.response_time_ms,
    )
    attempts = await store.list_recent_toeic_attempts(request.user_id, limit=10)
    next_item, recommended_difficulty, weak_tags, recent_accuracy = select_next_item(
        attempts=attempts,
        part_type=item.part_type,
        items=practice_items or TOEIC_ITEMS,
    )
    return ToeicAnswerResponse(
        item_id=request.item_id,
        correct=correct,
        correct_option=item.correct_option,
        explanation=item.explanation,
        grammar_tag=item.grammar_tag,
        vocab_tag=item.vocab_tag,
        weak_tags=weak_tags,
        recommended_difficulty=next_item.difficulty_level if correct else recommended_difficulty,
        recent_accuracy=recent_accuracy,
    )


async def launch_ready_pack(
    *,
    store: SqliteStore,
    ready_pack_id: str,
    request: ReadyPackLaunchRequest,
) -> ReadyPackLaunchResponse:
    ready_pack = await store.get_ready_pack(request.user_id, ready_pack_id)
    if ready_pack is None:
        raise ValueError(f"Ready pack {ready_pack_id} was not found")

    quiz_id = uuid4().hex
    await store.save_quiz_pack(request.user_id, quiz_id, ready_pack.pack)
    return ReadyPackLaunchResponse(
        ready_pack_id=ready_pack_id,
        quiz_id=quiz_id,
        pack=ready_pack.pack,
    )


async def analyze_image(
    *,
    model,
    store: SqliteStore,
    user_id: str,
    prompt: str,
    image_bytes: bytes,
    media_type: str,
    model_name: str | None = None,
) -> ImageAnalysisResponse:
    settings = get_settings()
    image_backend = resolve_backend_for_model_name(settings, model_name)
    if image_backend == "llama_cpp" and not settings.llama_vision_enabled:
        raise ValueError(
            "Image analysis is disabled for llama.cpp because LLAMA_VISION_ENABLED=false."
        )
    selected_model = build_model_for_name(settings, model_name) if model_name else model
    agent = build_vision_agent(selected_model)
    deps = ContentDeps(user_id=user_id, store=store)
    return await run_image_analysis(agent, prompt, image_bytes, media_type, deps)


async def queue_background_job(*, store: SqliteStore, request: QueueJobRequest) -> QueueJobResponse:
    if request.job_type == "prebuild_quiz":
        job = await enqueue_prebuild_job(
            store=store,
            user_id=request.user_id,
            topic=request.payload.get("topic", "Daily English review"),
            mode=request.payload.get("mode", "grammar"),
            difficulty=request.payload.get("difficulty", "medium"),
        )
    else:
        from .schemas import BackgroundJob

        job = BackgroundJob(user_id=request.user_id, job_type=request.job_type, payload=request.payload)
        await store.queue_job(job)
    return QueueJobResponse(job=job)


async def queue_problem_generation(*, store: SqliteStore, request: ProblemGenerationRequest) -> ProblemGenerationResponse:
    part_counts = {
        "part1": request.part1,
        "part2": request.part2,
        "part3": request.part3,
        "part4": request.part4,
        "part5": request.part5,
        "part6": request.part6,
        "part7": request.part7,
    }
    job = await enqueue_problem_generation_job(
        store,
        user_id=request.user_id,
        part_counts=part_counts,
    )
    return ProblemGenerationResponse(
        queued_job=job,
        requested_pack_count=sum(part_counts.values()),
    )


async def get_problem_inventory(
    *,
    store: SqliteStore,
    user_id: str,
    ready_pack_page: int = 1,
    practice_item_page: int = 1,
    page_size: int = 5,
) -> ProblemInventoryResponse:
    return await store.problem_inventory(
        user_id,
        ready_pack_page=ready_pack_page,
        practice_item_page=practice_item_page,
        page_size=page_size,
    )


async def get_ready_pack_detail(*, store: SqliteStore, user_id: str, ready_pack_id: str) -> ReadyPackDetail:
    detail = await store.get_ready_pack(user_id, ready_pack_id)
    if detail is None:
        raise ValueError(f"Ready pack {ready_pack_id} was not found")
    return detail


async def remove_ready_pack(*, store: SqliteStore, user_id: str, ready_pack_id: str) -> DeleteResourceResponse:
    deleted = await store.delete_ready_pack(user_id, ready_pack_id)
    if not deleted:
        raise ValueError(f"Ready pack {ready_pack_id} was not found")
    return DeleteResourceResponse(deleted=True, resource_id=ready_pack_id)


async def get_practice_item_detail(*, store: SqliteStore, user_id: str, item_id: str) -> PracticeItemDetail:
    detail = await store.get_practice_item(user_id, item_id)
    if detail is None:
        raise ValueError(f"Practice item {item_id} was not found")
    return detail


async def remove_practice_item(*, store: SqliteStore, user_id: str, item_id: str) -> DeleteResourceResponse:
    deleted = await store.delete_practice_item(user_id, item_id)
    if not deleted:
        raise ValueError(f"Practice item {item_id} was not found")
    return DeleteResourceResponse(deleted=True, resource_id=item_id)
