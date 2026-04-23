from __future__ import annotations

import json
from time import perf_counter
from uuid import uuid4

from .agents import (
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


async def handle_chat(*, model, store: SqliteStore, request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    selected_model = build_model_for_name(settings, request.model_name) if request.model_name else model
    selected_backend = resolve_backend_for_model_name(settings, request.model_name)
    active_model_name = request.model_name or (
        settings.llama_model if selected_backend == "llama_cpp" else settings.google_model
    )
    session_id = request.session_id or uuid4().hex
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
            },
            usage={},
        )
    agent = build_local_tutor_agent(selected_model) if selected_backend == "llama_cpp" else build_tutor_agent(selected_model)
    deps = TutorDeps(user_id=request.user_id, store=store)
    message_history = await store.load_chat_history(request.user_id, session_id)
    result = await agent.run(
        request.message,
        deps=deps,
        message_history=message_history,
        model_settings=_build_chat_model_settings(settings, selected_backend),
    )
    await store.save_chat_history(request.user_id, session_id, result.all_messages_json())
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
            "total_elapsed_ms": elapsed_ms,
        },
        usage=result.usage().opentelemetry_attributes(),
    )


def _build_chat_model_settings(settings, selected_backend: str) -> dict[str, object] | None:
    if selected_backend != "llama_cpp":
        return None
    model_settings: dict[str, object] = {
        "max_tokens": settings.llama_chat_max_tokens,
    }
    if settings.llama_chat_temperature is not None:
        model_settings["temperature"] = settings.llama_chat_temperature
    if settings.llama_chat_thinking_enabled:
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
    session_id = request.session_id or uuid4().hex

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
                            "first_chunk_ms": 0,
                            "total_elapsed_ms": 0,
                        },
                        usage={},
                    ).model_dump(mode="json"),
                }
            )

        return test_stream()

    agent = build_local_tutor_agent(selected_model) if selected_backend == "llama_cpp" else build_tutor_agent(selected_model)
    deps = TutorDeps(user_id=request.user_id, store=store)
    message_history = await store.load_chat_history(request.user_id, session_id)
    model_settings = _build_chat_model_settings(settings, selected_backend)

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
                await store.save_chat_history(request.user_id, session_id, result.all_messages_json())
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
                        "first_chunk_ms": first_chunk_ms,
                        "total_elapsed_ms": total_elapsed_ms,
                    },
                    usage=result.usage().opentelemetry_attributes(),
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
