from __future__ import annotations

from uuid import uuid4

from .agents import build_quiz_agent, build_tutor_agent, build_vision_agent, run_image_analysis
from .deps import ContentDeps, TutorDeps
from .jobs import enqueue_prebuild_job
from .schemas import (
    ChatRequest,
    ChatResponse,
    ImageAnalysisResponse,
    QueueJobRequest,
    QueueJobResponse,
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
from .toeic import get_item_by_id, select_next_item


async def handle_chat(*, model, store: SqliteStore, request: ChatRequest) -> ChatResponse:
    agent = build_tutor_agent(model)
    deps = TutorDeps(user_id=request.user_id, store=store)
    session_id = request.session_id or uuid4().hex
    result = await agent.run(request.message, deps=deps)
    for item in result.output.memory_to_store:
        await store.add_memory(request.user_id, item)
    return ChatResponse(
        session_id=session_id,
        run_id=result.run_id,
        output=result.output,
        usage=result.usage().opentelemetry_attributes(),
    )


async def generate_quiz(*, model, store: SqliteStore, request: QuizGenerateRequest) -> QuizGenerateResponse:
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
    item, recommended_difficulty, weak_tags, recent_accuracy = select_next_item(
        attempts=attempts,
        part_type=request.part_type,
    )
    return ToeicNextResponse(
        item=item,
        recommended_difficulty=recommended_difficulty,
        weak_tags=weak_tags,
        recent_accuracy=recent_accuracy,
    )


async def submit_toeic_answer(*, store: SqliteStore, request: ToeicAnswerRequest) -> ToeicAnswerResponse:
    item = get_item_by_id(request.item_id)
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


async def analyze_image(
    *,
    model,
    store: SqliteStore,
    user_id: str,
    prompt: str,
    image_bytes: bytes,
    media_type: str,
) -> ImageAnalysisResponse:
    agent = build_vision_agent(model)
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
