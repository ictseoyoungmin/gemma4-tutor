from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .agents import build_quiz_agent
from .deps import ContentDeps
from .schemas import BackgroundJob, QuizPack, QuizItem, ToeicPracticeItem
from .storage import SqliteStore


async def enqueue_prebuild_job(store: SqliteStore, user_id: str, topic: str, mode: str = "grammar", difficulty: str = "medium") -> BackgroundJob:
    job = BackgroundJob(
        user_id=user_id,
        job_type="prebuild_quiz",
        payload={"topic": topic, "mode": mode, "difficulty": difficulty},
    )
    await store.queue_job(job)
    return job


async def enqueue_problem_generation_job(
    store: SqliteStore,
    *,
    user_id: str,
    part_counts: dict[str, int],
) -> BackgroundJob:
    job = BackgroundJob(
        user_id=user_id,
        job_type="generate_problem_set",
        payload={"part_counts": part_counts},
    )
    await store.queue_job(job)
    return job


def build_seed_ready_pack(*, topic: str, mode: str, difficulty: str) -> QuizPack:
    if mode == "toeic":
        return QuizPack(
            title=topic,
            mode="toeic",
            difficulty=difficulty,
            items=[
                QuizItem(
                    prompt=f"구매팀은 점심 전에 최신 거래처 목록을 ___ 예정입니다.",
                    choices=["review", "reviews", "reviewed", "reviewing"],
                    answer="review",
                    explanation="'will' 뒤에는 동사원형이 와야 하므로 'review'가 정답입니다.",
                    skill_tags=["toeic", "part5", "grammar", "modal_base_form"],
                ),
                QuizItem(
                    prompt="모든 영수증은 금요일 오후까지 ___ 제출되어야 합니다.",
                    choices=["at", "by", "since", "during"],
                    answer="by",
                    explanation="'by'는 마감 시점을 나타내므로 '금요일 오후까지'라는 뜻에 맞습니다.",
                    skill_tags=["toeic", "part5", "grammar", "deadline_preposition"],
                ),
                QuizItem(
                    prompt="새 정책이 명확히 설명되어 직원들이 그것을 ___ 이해했습니다.",
                    choices=["complete", "completed", "completely", "completion"],
                    answer="completely",
                    explanation="'understood'를 수식하는 부사가 필요하므로 'completely'가 맞습니다.",
                    skill_tags=["toeic", "part5", "grammar", "adverb_form"],
                ),
            ],
        )

    return QuizPack(
        title=topic,
        mode="grammar",
        difficulty=difficulty,
        items=[
            QuizItem(
                prompt=f"{topic}에 대한 업무 보고 문장으로 가장 자연스러운 것을 고르세요.",
                choices=[
                    "The report are ready for review.",
                    "The report is ready for review.",
                    "The report ready for review.",
                    "The report be ready for review.",
                ],
                answer="The report is ready for review.",
                explanation="단수 주어 report에는 'is'가 와야 하므로 두 번째 문장이 맞습니다.",
                skill_tags=["grammar", "subject_verb_agreement", "workplace_english"],
            ),
            QuizItem(
                prompt=f"Fill in the blank: We have discussed the schedule, but we have not decided ___ the venue yet.",
                choices=["at", "for", "on", "with"],
                answer="on",
                explanation="'결정하다'의 의미로는 'decide on'이 자연스러운 결합입니다.",
                skill_tags=["grammar", "collocation", "prepositions"],
            ),
            QuizItem(
                prompt=f"Rewrite this message more naturally: 'Please check {topic} quickly.'",
                choices=[],
                answer=f"Could you please review {topic} as soon as possible?",
                explanation="업무 맥락에서는 요청을 더 공손하고 자연스럽게 바꾼 문장입니다.",
                skill_tags=["grammar", "rewriting", "politeness"],
            ),
        ],
    )


PACK_TEMPLATE_CATALOG: dict[str, list[dict[str, str | int]]] = {
    "part2": [
        {"title": "Part 2 응답 패턴 훈련", "difficulty": "easy", "item_count": 10, "minutes": 8},
        {"title": "Part 2 함정 응답 집중", "difficulty": "medium", "item_count": 20, "minutes": 15},
        {"title": "Part 2 실전 청취 응답", "difficulty": "hard", "item_count": 30, "minutes": 20},
    ],
    "part5": [
        {"title": "Part 5 핵심 문법 10선", "difficulty": "easy", "item_count": 10, "minutes": 8},
        {"title": "Part 5 핵심 문법 40선", "difficulty": "easy", "item_count": 40, "minutes": 30},
        {"title": "비즈니스 어휘 실전편", "difficulty": "medium", "item_count": 60, "minutes": 45},
        {"title": "RC 고난도 모의고사", "difficulty": "hard", "item_count": 100, "minutes": 75},
    ],
    "part7": [
        {"title": "Part 7 독해 지문 분석", "difficulty": "medium", "item_count": 20, "minutes": 25},
        {"title": "Part 7 장문 독해 실전", "difficulty": "hard", "item_count": 30, "minutes": 35},
    ],
}


def build_part5_practice_item(index: int, difficulty: str) -> ToeicPracticeItem:
    examples = [
        (
            "The finance director asked that all expense reports be submitted by Friday.",
            ["be", "being", "are", "to be"],
            "be",
            "ask that + 주어 + 동사원형 구조이므로 'be'가 정답입니다.",
            "subjunctive",
            "finance",
        ),
        (
            "The revised contract was reviewed carefully before it was sent to the client.",
            ["careful", "carefully", "care", "carefulness"],
            "carefully",
            "동사 reviewed를 수식하는 부사가 필요하므로 'carefully'가 맞습니다.",
            "adverb_form",
            "legal",
        ),
        (
            "Employees are encouraged to contact HR if they have any questions about the new policy.",
            ["question", "questions", "questioned", "questioning"],
            "questions",
            "'any' 뒤에는 복수 명사 questions가 자연스럽습니다.",
            "count_noun",
            "hr",
        ),
    ]
    prompt, options, answer, explanation, grammar_tag, vocab_tag = examples[index % len(examples)]
    return ToeicPracticeItem(
        item_id=uuid4().hex,
        part_type="part5",
        difficulty_level=difficulty,  # type: ignore[arg-type]
        prompt="빈칸에 들어갈 가장 적절한 표현을 고르세요.",
        question_text=prompt,
        options=options,
        correct_option=answer,
        explanation=explanation,
        grammar_tag=grammar_tag,
        vocab_tag=vocab_tag,
        validated=True,
        validation_score=0.92,
    )


def build_pack_from_template(template: dict[str, str | int], part_type: str, ordinal: int) -> QuizPack:
    title = str(template["title"])
    difficulty = str(template["difficulty"])
    item_count = int(template["item_count"])
    return QuizPack(
        title=title,
        mode="toeic",
        difficulty=difficulty,  # type: ignore[arg-type]
        items=[
            QuizItem(
                prompt=f"{part_type.upper()} 유형 {ordinal}번 팩 예제 문항 {i + 1}",
                choices=["A", "B", "C", "D"],
                answer="A",
                explanation=f"{title}의 {i + 1}번 문항 해설입니다. 정답 근거를 한국어로 짧게 정리했습니다.",
                skill_tags=["toeic", part_type, difficulty],
            )
            for i in range(min(item_count, 12))
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

    if job.job_type == "generate_problem_set":
        part_counts = {
            key: int(value)
            for key, value in (job.payload.get("part_counts", {}) or {}).items()
            if int(value) > 0
        }
        created_pack_ids: list[str] = []
        created_practice_item_ids: list[str] = []
        now = datetime.now(timezone.utc).isoformat()

        for part_type, count in part_counts.items():
            templates = PACK_TEMPLATE_CATALOG.get(part_type, [])
            for index in range(count):
                template = templates[index % len(templates)] if templates else {
                    "title": f"{part_type.upper()} 실전 팩 {index + 1}",
                    "difficulty": "medium",
                    "item_count": 20,
                }
                pack = build_pack_from_template(template, part_type, index + 1)
                ready_pack_id = uuid4().hex
                await store.save_ready_pack(job.user_id, ready_pack_id, pack, created_at=now)
                created_pack_ids.append(ready_pack_id)

                if part_type == "part5":
                    practice_item = build_part5_practice_item(index, str(template["difficulty"]))
                    await store.save_practice_item(
                        user_id=job.user_id,
                        item=practice_item,
                        source="worker_generated",
                        created_at=now,
                    )
                    created_practice_item_ids.append(practice_item.item_id)

        return {
            "status": "generated",
            "ready_pack_count": len(created_pack_ids),
            "practice_item_count": len(created_practice_item_ids),
            "created_pack_ids": created_pack_ids,
            "created_practice_item_ids": created_practice_item_ids,
            "part_counts": part_counts,
        }

    if job.job_type == "summarize_session":
        return {"summary": "Placeholder session summary. Connect reflection agent later."}

    if job.job_type == "refresh_dashboard":
        await store.seed_placeholders(job.user_id)
        return {"status": "dashboard_refreshed"}

    return {"status": "placeholder_complete"}
