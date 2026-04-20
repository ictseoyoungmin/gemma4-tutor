from __future__ import annotations

from datetime import datetime, timezone
import re
from uuid import uuid4

from .agents import build_quiz_agent
from .deps import ContentDeps
from .harness.runner import validate_generated_pack
from .schemas import BackgroundJob, QuizPack, QuizItem, ToeicPracticeItem
from .storage import SqliteStore


HANGUL_PATTERN = re.compile(r"[가-힣]")


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
                    prompt="The purchasing team will ___ the updated vendor list before lunch.",
                    choices=["review", "reviews", "reviewed", "reviewing"],
                    answer="review",
                    explanation="'will' 뒤에는 동사원형이 와야 하므로 'review'가 정답입니다.",
                    skill_tags=["toeic", "part5", "grammar", "modal_base_form"],
                ),
                QuizItem(
                    prompt="All receipts must be submitted ___ Friday afternoon.",
                    choices=["at", "by", "since", "during"],
                    answer="by",
                    explanation="'by'는 마감 시점을 나타내므로 '금요일 오후까지'라는 뜻에 맞습니다.",
                    skill_tags=["toeic", "part5", "grammar", "deadline_preposition"],
                ),
                QuizItem(
                    prompt="The new policy was explained clearly, so employees understood it ___.",
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
                prompt=f"Choose the most natural sentence for a workplace update about {topic}.",
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


def contains_hangul(text: str) -> bool:
    return bool(HANGUL_PATTERN.search(text))


def make_unique_title(base_title: str, existing_titles: set[str]) -> str:
    if base_title not in existing_titles:
        existing_titles.add(base_title)
        return base_title
    suffix = 2
    while f"{base_title} ({suffix})" in existing_titles:
        suffix += 1
    unique_title = f"{base_title} ({suffix})"
    existing_titles.add(unique_title)
    return unique_title


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


def build_practice_item_from_pack(pack: QuizPack, difficulty: str, index: int) -> ToeicPracticeItem:
    source_item = pack.items[index % len(pack.items)]
    if len(source_item.choices) == 4 and source_item.answer in source_item.choices:
        return ToeicPracticeItem(
            item_id=uuid4().hex,
            part_type="part5",
            difficulty_level=difficulty,  # type: ignore[arg-type]
            prompt="Choose the best answer to complete the sentence.",
            question_text=source_item.prompt,
            options=source_item.choices,
            correct_option=source_item.answer,
            explanation=source_item.explanation,
            grammar_tag="worker_generated_part5",
            vocab_tag="toeic",
            validated=True,
            validation_score=0.9,
        )
    return build_part5_practice_item(index, difficulty)


def get_template_example_bank(part_type: str) -> list[tuple[str, list[str], str, str]]:
    if part_type == "part2":
        return [
            (
                "Where is the orientation schedule posted?",
                [
                    "It is on the bulletin board by the lobby.",
                    "Yes, the schedule was updated yesterday.",
                    "No, I have not posted the package yet.",
                    "At 9 a.m. every Monday morning.",
                ],
                "It is on the bulletin board by the lobby.",
                "질문이 장소를 묻고 있으므로 위치에 직접 답하는 문장이 정답입니다.",
            ),
            (
                "Who approved the revised travel budget?",
                [
                    "The finance director signed it this morning.",
                    "It costs less than last year's budget.",
                    "Yes, the budget report was helpful.",
                    "We usually travel by train.",
                ],
                "The finance director signed it this morning.",
                "질문이 사람을 묻고 있으므로 승인한 사람을 답하는 선택지가 맞습니다.",
            ),
            (
                "Why was the client meeting postponed?",
                [
                    "Because the lead presenter was stuck at the airport.",
                    "In the main conference room on the third floor.",
                    "Yes, the client liked the proposal.",
                    "For about thirty minutes after lunch.",
                ],
                "Because the lead presenter was stuck at the airport.",
                "질문이 이유를 묻고 있으므로 원인을 설명하는 응답이 정답입니다.",
            ),
            (
                "When will the maintenance team inspect the elevators?",
                [
                    "They are scheduled to check them tonight after 8 p.m.",
                    "The inspection report was very detailed.",
                    "Yes, the team has already arrived.",
                    "Near the employee entrance on the first floor.",
                ],
                "They are scheduled to check them tonight after 8 p.m.",
                "질문이 시간을 묻고 있으므로 점검 시점을 말하는 선택지가 자연스럽습니다.",
            ),
        ]
    if part_type == "part7":
        return [
            (
                "Email excerpt: The accounting team will close the monthly expense report at 5 p.m. on Thursday. "
                "Any missing receipts must be uploaded before that deadline.\n"
                "Question: What should employees do before Thursday evening?",
                [
                    "Upload any missing receipts.",
                    "Meet the accounting team in person.",
                    "Print the final expense report.",
                    "Ask for a later closing time.",
                ],
                "Upload any missing receipts.",
                "지문에서 목요일 오후 5시 전까지 누락 영수증을 업로드해야 한다고 직접 말하고 있습니다.",
            ),
            (
                "Notice: The west parking garage will be closed for repainting from May 3 to May 5. "
                "Employees should use the east garage during this period.\n"
                "Question: Where should employees park during the repainting work?",
                [
                    "In the east parking garage.",
                    "On the roof of the west garage.",
                    "In the visitor lot only.",
                    "Beside the loading dock.",
                ],
                "In the east parking garage.",
                "공사 기간 동안 동쪽 주차장을 이용하라고 안내문에 명시되어 있습니다.",
            ),
            (
                "Memo: Please submit all booth design changes by Friday noon so the print vendor can finalize the event banners.\n"
                "Question: Why is Friday noon important?",
                [
                    "The print vendor needs time to finalize the banners.",
                    "The event opens to visitors at that exact time.",
                    "The design team is leaving for a workshop.",
                    "The budget meeting starts before lunch.",
                ],
                "The print vendor needs time to finalize the banners.",
                "배너 인쇄를 마무리할 시간이 필요하기 때문에 금요일 정오가 마감 시한입니다.",
            ),
            (
                "Article snippet: Customer service representatives will begin using the new ticket system next Monday. "
                "A training video and quick-reference guide will be shared on Friday.\n"
                "Question: What will staff receive on Friday?",
                [
                    "A training video and a quick-reference guide.",
                    "Their finalized Monday work schedules.",
                    "A list of customer complaints from last week.",
                    "An invitation to a budget planning seminar.",
                ],
                "A training video and a quick-reference guide.",
                "금요일에 전달되는 자료로 training video와 quick-reference guide가 제시되어 있습니다.",
            ),
        ]
    if part_type == "part6":
        return [
            (
                "The marketing team plans to ___ the updated campaign calendar before the regional meeting.",
                ["share", "shares", "shared", "sharing"],
                "share",
                "to 뒤에는 동사원형이 와야 하므로 'share'가 정답입니다.",
            ),
            (
                "Please review the attached draft carefully and send your feedback ___ Friday afternoon.",
                ["by", "until", "among", "upon"],
                "by",
                "마감 시점을 나타내는 표현으로는 'by Friday afternoon'이 자연스럽습니다.",
            ),
            (
                "Because demand increased suddenly, the supplier requested an ___ delivery schedule.",
                ["adjusted", "adjust", "adjusting", "adjustment"],
                "adjusted",
                "delivery schedule를 꾸미는 형용사 역할이 필요하므로 'adjusted'가 알맞습니다.",
            ),
            (
                "The proposal was concise, informative, and easy to ___ during the client briefing.",
                ["follow", "follows", "followed", "following"],
                "follow",
                "easy to 뒤에는 동사원형이 오므로 'follow'가 맞습니다.",
            ),
        ]
    return [
        (
            "The annual budget will ___ finalized next week.",
            ["be", "is", "are", "was"],
            "be",
            "'will' 뒤에는 동사원형이 와야 하므로 'be'가 정답입니다.",
        ),
        (
            "Applicants should ___ the completed form before Friday.",
            ["submit", "submits", "submitted", "submitting"],
            "submit",
            "조동사 should 뒤에는 동사원형이 오므로 'submit'이 맞습니다.",
        ),
        (
            "The manager spoke so ___ that everyone understood the new policy.",
            ["clearly", "clear", "clearness", "cleared"],
            "clearly",
            "동사를 수식하는 부사가 필요하므로 'clearly'가 정답입니다.",
        ),
        (
            "The vendor asked us to confirm the shipment date ___ the contract was signed.",
            ["after", "while", "between", "unless"],
            "after",
            "문맥상 계약 체결 이후 시점을 나타내는 'after'가 자연스럽습니다.",
        ),
    ]


def build_pack_from_template(template: dict[str, str | int], part_type: str, ordinal: int) -> QuizPack:
    title = str(template["title"])
    difficulty = str(template["difficulty"])
    item_count = int(template["item_count"])
    example_bank = get_template_example_bank(part_type)
    return QuizPack(
        title=title,
        mode="toeic",
        difficulty=difficulty,  # type: ignore[arg-type]
        items=[
            QuizItem(
                prompt=example_bank[i % len(example_bank)][0],
                choices=example_bank[i % len(example_bank)][1],
                answer=example_bank[i % len(example_bank)][2],
                explanation=example_bank[i % len(example_bank)][3],
                skill_tags=["toeic", part_type, difficulty],
            )
            for i in range(item_count)
        ],
    )


def build_problem_set_fallback_pack(
    *,
    template: dict[str, str | int],
    part_type: str,
    unique_title: str,
    ordinal: int,
) -> QuizPack:
    return build_pack_from_template(
        {**template, "title": unique_title},
        part_type,
        ordinal,
    )


def validate_quiz_pack(
    pack: QuizPack,
    *,
    require_english_items: bool = False,
    require_korean_explanations: bool = False,
) -> list[str]:
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
        if require_english_items:
            if contains_hangul(item.prompt):
                errors.append(f"item_{index}_prompt_not_english")
            if any(contains_hangul(choice) for choice in item.choices):
                errors.append(f"item_{index}_choice_not_english")
            if contains_hangul(item.answer):
                errors.append(f"item_{index}_answer_not_english")
        if require_korean_explanations and not contains_hangul(item.explanation):
            errors.append(f"item_{index}_explanation_not_korean")
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


async def generate_ready_pack(
    *,
    store: SqliteStore,
    model,
    user_id: str,
    topic: str,
    mode: str,
    difficulty: str,
    item_count: int = 3,
    part_type: str = "part5",
) -> tuple[QuizPack, dict]:
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
        if mode == "toeic":
            prompt = (
                f'Create a TOEIC {part_type.upper()} ready pack with the exact Korean title "{topic}". '
                f"Difficulty: {difficulty}. Count: {item_count}. "
                "All questions, answer choices, and correct answers must be written in English only. "
                "All explanations must be written in Korean only. "
                "Keep every item practical and test-like, not placeholder content. "
                "Return a fully structured pack."
            )
        else:
            prompt = (
                f'Create an English learning ready pack with the exact Korean title "{topic}". '
                f"Difficulty: {difficulty}. Count: {item_count}. "
                "All question bodies and answer content should be written in English. "
                "All explanations must be written in Korean only. "
                "Return a fully structured pack."
            )
        try:
            result = await agent.run(prompt, deps=deps)
            candidate_pack = result.output.model_copy(
                update={
                    "title": topic,
                    "mode": mode,
                    "difficulty": difficulty,
                }
            )
            validation_errors = validate_quiz_pack(
                candidate_pack,
                require_english_items=True,
                require_korean_explanations=True,
            )
            harness_result = validate_generated_pack(
                candidate_pack,
                require_english_items=True,
                require_korean_explanations=True,
            )
            generation_meta["validation_errors"] = validation_errors
            generation_meta["harness"] = harness_result
            if not validation_errors and harness_result["passed"]:
                generation_meta["strategy"] = "llm"
                generation_meta["validated"] = True
                return candidate_pack, generation_meta
            generation_meta["strategy"] = "llm_invalid_fallback"
        except Exception as exc:  # noqa: BLE001
            generation_meta["strategy"] = "llm_error_fallback"
            generation_meta["error"] = str(exc)

    seed_pack = build_seed_ready_pack(topic=topic, mode=mode, difficulty=difficulty)
    if generation_meta["strategy"] == "seed_fallback":
        generation_meta["validation_errors"] = validate_quiz_pack(
            seed_pack,
            require_english_items=True,
            require_korean_explanations=True,
        )
        generation_meta["harness"] = validate_generated_pack(
            seed_pack,
            require_english_items=True,
            require_korean_explanations=True,
        )
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
            generation_meta=generation_meta,
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
        existing_titles = {pack.title for pack in await store.list_ready_packs(job.user_id, limit=500)}
        per_part_sequence = {
            part_type: len([title for title in existing_titles if title.startswith(part_type.upper())])
            for part_type in part_counts
        }

        for part_type, count in part_counts.items():
            templates = PACK_TEMPLATE_CATALOG.get(part_type, [])
            for index in range(count):
                template_index = index % len(templates) if templates else 0
                template = templates[template_index] if templates else {
                    "title": f"{part_type.upper()} 실전 팩 {per_part_sequence.get(part_type, 0) + index + 1}",
                    "difficulty": "medium",
                    "item_count": 20,
                }
                base_title = str(template["title"])
                unique_title = make_unique_title(base_title, existing_titles)
                difficulty = str(template["difficulty"])
                item_count = int(template["item_count"])
                pack, generation_meta = await generate_ready_pack(
                    store=store,
                    model=model,
                    user_id=job.user_id,
                    topic=unique_title,
                    mode="toeic",
                    difficulty=difficulty,
                    item_count=item_count,
                    part_type=part_type,
                )
                if generation_meta["strategy"] != "llm":
                    pack = build_problem_set_fallback_pack(
                        template=template,
                        part_type=part_type,
                        unique_title=unique_title,
                        ordinal=per_part_sequence.get(part_type, 0) + index + 1,
                    )
                ready_pack_id = uuid4().hex
                await store.save_ready_pack(
                    job.user_id,
                    ready_pack_id,
                    pack,
                    created_at=now,
                    generation_meta=generation_meta,
                )
                created_pack_ids.append(ready_pack_id)

                if part_type == "part5":
                    practice_item = build_practice_item_from_pack(pack, difficulty, index)
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
