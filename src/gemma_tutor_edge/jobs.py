from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

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


async def process_job(*, store: SqliteStore, model, job: BackgroundJob) -> dict:
    """Placeholder worker path.

    The implementation intentionally keeps one deterministic path so the system can be demoed
    before the full agentic background generation is wired in.
    """
    if job.job_type == "prebuild_quiz":
        topic = job.payload.get("topic", "Daily English review")
        mode = job.payload.get("mode", "grammar")
        difficulty = job.payload.get("difficulty", "medium")
        pack = QuizPack(
            title=f"Ready Pack: {topic}",
            mode=mode,
            difficulty=difficulty,
            items=[
                QuizItem(
                    prompt=f"Placeholder question 1 about {topic}",
                    choices=["A", "B", "C", "D"],
                    answer="A",
                    explanation="Placeholder explanation. Replace with LLM-generated rationale.",
                    skill_tags=[mode, "review"],
                ),
                QuizItem(
                    prompt=f"Placeholder question 2 about {topic}",
                    choices=[],
                    answer="sample answer",
                    explanation="Placeholder free-response explanation.",
                    skill_tags=[mode],
                ),
            ],
        )
        ready_pack_id = uuid4().hex
        await store.save_ready_pack(
            job.user_id,
            ready_pack_id,
            pack,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"ready_pack_id": ready_pack_id, "status": "prebuilt", "item_count": len(pack.items)}

    if job.job_type == "summarize_session":
        return {"summary": "Placeholder session summary. Connect reflection agent later."}

    if job.job_type == "refresh_dashboard":
        await store.seed_placeholders(job.user_id)
        return {"status": "dashboard_refreshed"}

    return {"status": "placeholder_complete"}
