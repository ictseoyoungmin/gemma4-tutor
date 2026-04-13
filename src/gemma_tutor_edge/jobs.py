from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .agents import build_quiz_agent
from .deps import ContentDeps
from .schemas import BackgroundJob, QuizPack, QuizItem
from .storage import SqliteStore


async def enqueue_prebuild_job(store: SqliteStore, user_id: str, topic: str, mode: str = "grammar", difficulty: str = "medium") -> BackgroundJob:
    job = BackgroundJob(
        user_id=user_id,
        job_type="prebuild_quiz",
        payload={"topic": topic, "mode": mode, "difficulty": difficulty},
    )
    await store.queue_job(job)
    return job


def build_seed_ready_pack(*, topic: str, mode: str, difficulty: str) -> QuizPack:
    if mode == "toeic":
        return QuizPack(
            title=f"Ready Pack: {topic}",
            mode="toeic",
            difficulty=difficulty,
            items=[
                QuizItem(
                    prompt=f"The purchasing team will ___ the updated vendor list before lunch. ({topic})",
                    choices=["review", "reviews", "reviewed", "reviewing"],
                    answer="review",
                    explanation="After 'will', use the base form of the verb.",
                    skill_tags=["toeic", "part5", "grammar", "modal_base_form"],
                ),
                QuizItem(
                    prompt=f"All receipts must be submitted ___ Friday afternoon. ({topic})",
                    choices=["at", "by", "since", "during"],
                    answer="by",
                    explanation="'By' sets a deadline that must be met before the stated time.",
                    skill_tags=["toeic", "part5", "grammar", "deadline_preposition"],
                ),
                QuizItem(
                    prompt=f"The new policy was explained clearly, so employees understood it ___. ({topic})",
                    choices=["complete", "completed", "completely", "completion"],
                    answer="completely",
                    explanation="The verb 'understood' is modified by an adverb, so 'completely' fits.",
                    skill_tags=["toeic", "part5", "grammar", "adverb_form"],
                ),
            ],
        )

    return QuizPack(
        title=f"Ready Pack: {topic}",
        mode="grammar",
        difficulty=difficulty,
        items=[
            QuizItem(
                prompt=f"Choose the best sentence for a workplace update about {topic}.",
                choices=[
                    "The report are ready for review.",
                    "The report is ready for review.",
                    "The report ready for review.",
                    "The report be ready for review.",
                ],
                answer="The report is ready for review.",
                explanation="A singular subject takes 'is', so the full grammatical sentence is the second option.",
                skill_tags=["grammar", "subject_verb_agreement", "workplace_english"],
            ),
            QuizItem(
                prompt=f"Fill in the blank: We have discussed the schedule, but we have not decided ___ the venue yet.",
                choices=["at", "for", "on", "with"],
                answer="on",
                explanation="The collocation is 'decide on' when selecting an option.",
                skill_tags=["grammar", "collocation", "prepositions"],
            ),
            QuizItem(
                prompt=f"Rewrite this message more naturally: 'Please check {topic} quickly.'",
                choices=[],
                answer=f"Could you please review {topic} as soon as possible?",
                explanation="This rewrite is more polite and natural for workplace English.",
                skill_tags=["grammar", "rewriting", "politeness"],
            ),
        ],
    )


def validate_quiz_pack(pack: QuizPack) -> list[str]:
    errors: list[str] = []
    if not pack.title.strip():
        errors.append("missing_title")
    if len(pack.items) < 3:
        errors.append("too_few_items")
    for index, item in enumerate(pack.items):
        if not item.prompt.strip():
            errors.append(f"item_{index}_missing_prompt")
        if not item.explanation.strip():
            errors.append(f"item_{index}_missing_explanation")
        if item.choices:
            if len(item.choices) != 4:
                errors.append(f"item_{index}_invalid_choice_count")
            if len(set(item.choices)) != len(item.choices):
                errors.append(f"item_{index}_duplicate_choices")
            if item.answer not in item.choices:
                errors.append(f"item_{index}_answer_not_in_choices")
        elif not item.answer.strip():
            errors.append(f"item_{index}_missing_answer")
    return errors


async def generate_ready_pack(*, store: SqliteStore, model, user_id: str, topic: str, mode: str, difficulty: str) -> tuple[QuizPack, dict]:
    generation_meta: dict[str, object] = {
        "topic": topic,
        "mode": mode,
        "difficulty": difficulty,
        "strategy": "seed_fallback",
        "validated": False,
        "validation_errors": [],
    }

    if model != "test":
        agent = build_quiz_agent(model)
        deps = ContentDeps(user_id=user_id, store=store)
        prompt = (
            f"Create a {mode} ready pack about {topic}. "
            f"Difficulty: {difficulty}. Count: 3. "
            "Prefer workplace English. Include concise explanations."
        )
        try:
            result = await agent.run(prompt, deps=deps)
            candidate_pack = result.output
            validation_errors = validate_quiz_pack(candidate_pack)
            generation_meta["validation_errors"] = validation_errors
            if not validation_errors:
                generation_meta["strategy"] = "llm"
                generation_meta["validated"] = True
                return candidate_pack, generation_meta
            generation_meta["strategy"] = "llm_invalid_fallback"
        except Exception as exc:  # noqa: BLE001
            generation_meta["strategy"] = "llm_error_fallback"
            generation_meta["error"] = str(exc)

    seed_pack = build_seed_ready_pack(topic=topic, mode=mode, difficulty=difficulty)
    generation_meta["validation_errors"] = validate_quiz_pack(seed_pack)
    generation_meta["validated"] = True
    return seed_pack, generation_meta


async def process_job(*, store: SqliteStore, model, job: BackgroundJob) -> dict:
    if job.job_type == "prebuild_quiz":
        topic = job.payload.get("topic", "Daily English review")
        mode = job.payload.get("mode", "grammar")
        difficulty = job.payload.get("difficulty", "medium")
        pack, generation_meta = await generate_ready_pack(
            store=store,
            model=model,
            user_id=job.user_id,
            topic=topic,
            mode=mode,
            difficulty=difficulty,
        )
        ready_pack_id = uuid4().hex
        await store.save_ready_pack(
            job.user_id,
            ready_pack_id,
            pack,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return {
            "ready_pack_id": ready_pack_id,
            "status": "prebuilt",
            "item_count": len(pack.items),
            "generation": generation_meta,
        }

    if job.job_type == "summarize_session":
        return {"summary": "Placeholder session summary. Connect reflection agent later."}

    if job.job_type == "refresh_dashboard":
        await store.seed_placeholders(job.user_id)
        return {"status": "dashboard_refreshed"}

    return {"status": "placeholder_complete"}
