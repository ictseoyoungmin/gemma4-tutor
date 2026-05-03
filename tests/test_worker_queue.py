from pathlib import Path
import re

import pytest

import gemma_tutor_edge.jobs as jobs_module
from gemma_tutor_edge.jobs import (
    build_part5_practice_item,
    build_pack_from_template,
    build_seed_ready_pack,
    build_toeic_ready_pack_prompt,
    enqueue_prebuild_job,
    enqueue_problem_generation_job,
    generate_ready_pack,
    normalize_pack_answers,
    process_job,
    split_generation_counts,
    validate_quiz_pack,
)
from gemma_tutor_edge.harness.runner import validate_generated_pack
from gemma_tutor_edge.schemas import QuizItem, QuizPack
from gemma_tutor_edge.schemas import ReadyPackLaunchRequest
from gemma_tutor_edge.services import launch_ready_pack
from gemma_tutor_edge.storage import SqliteStore


HANGUL_PATTERN = re.compile(r"[가-힣]")
COUNT_PATTERN = re.compile(r"Count: (\d+)\.")


@pytest.mark.asyncio
async def test_worker_creates_ready_pack(tmp_path: Path):
    store = SqliteStore(tmp_path / "worker.db")
    await store.init()
    job = await enqueue_prebuild_job(store, user_id="u1", topic="travel English")
    fetched = await store.fetch_next_job()
    assert fetched is not None
    result = await process_job(store=store, model="test", job=fetched)
    assert result["status"] == "prebuilt"
    assert result["generation"]["strategy"] == "seed_fallback"
    assert result["generation"]["validated"] is True
    assert result["generation"]["harness"]["passed"] is True
    assert result["item_count"] >= 3
    ready = await store.list_ready_packs("u1")
    assert len(ready) == 1

    launched = await launch_ready_pack(
        store=store,
        ready_pack_id=ready[0].ready_pack_id,
        request=ReadyPackLaunchRequest(user_id="u1"),
    )
    assert launched.ready_pack_id == ready[0].ready_pack_id
    assert launched.quiz_id
    assert len(launched.pack.items) >= 3
    assert all(item.explanation for item in launched.pack.items)


@pytest.mark.asyncio
async def test_worker_generates_problem_set_with_ready_packs_and_practice_items(tmp_path: Path):
    store = SqliteStore(tmp_path / "problem-set.db")
    await store.init()
    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part2": 2, "part5": 3},
    )
    result = await process_job(store=store, model="test", job=job)
    assert result["status"] == "generated"
    assert result["ready_pack_count"] == 5
    assert result["practice_item_count"] == 3

    inventory = await store.problem_inventory("u1")
    assert inventory.stats.total_ready_packs == 5
    assert inventory.stats.total_practice_items == 3
    assert inventory.stats.practice_items_by_part["part5"] == 3
    assert len({pack.title for pack in inventory.ready_packs}) == len(inventory.ready_packs)

    launched = await launch_ready_pack(
        store=store,
        ready_pack_id=inventory.ready_packs[0].ready_pack_id,
        request=ReadyPackLaunchRequest(user_id="u1"),
    )
    assert all(not HANGUL_PATTERN.search(item.prompt) for item in launched.pack.items)
    assert all(HANGUL_PATTERN.search(item.explanation) for item in launched.pack.items)


@pytest.mark.asyncio
async def test_worker_avoids_duplicate_titles_across_multiple_generation_batches(tmp_path: Path):
    store = SqliteStore(tmp_path / "duplicate-titles.db")
    await store.init()

    first_job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part6": 1, "part5": 1},
    )
    second_job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part6": 1, "part5": 1},
    )

    await process_job(store=store, model="test", job=first_job)
    await process_job(store=store, model="test", job=second_job)

    ready = await store.list_ready_packs("u1", limit=10)
    titles = [pack.title for pack in ready]
    assert len(titles) == len(set(titles))


class _FakeAgentResult:
    def __init__(self, output: QuizPack):
        self.output = output


class _FakeAgent:
    def __init__(self, *, output: QuizPack | None = None, error: Exception | None = None):
        self.output = output
        self.error = error

    async def run(self, prompt: str, deps):  # noqa: ANN001
        if self.error is not None:
            raise self.error
        assert self.output is not None
        return _FakeAgentResult(self.output)


class _ChunkedFakeAgent:
    def __init__(self):
        self.prompts: list[str] = []

    async def run(self, prompt: str, deps):  # noqa: ANN001
        self.prompts.append(prompt)
        count_match = COUNT_PATTERN.search(prompt)
        assert count_match is not None
        chunk_count = int(count_match.group(1))
        items = [
            QuizItem(
                prompt=f"The operations team will ___ task {index + 1}.",
                choices=["review", "reviews", "reviewed", "reviewing"],
                answer="review",
                explanation="'will' 뒤에는 동사원형이 와야 하므로 'review'가 정답입니다.",
                skill_tags=["toeic", "part7", "grammar"],
            )
            for index in range(chunk_count)
        ]
        return _FakeAgentResult(
            QuizPack(
                title="ignored",
                mode="toeic",
                difficulty="medium",
                items=items,
            )
        )


class _QueuedFakeAgent:
    def __init__(self, outputs: list[QuizPack]):
        self.outputs = outputs
        self.prompts: list[str] = []

    async def run(self, prompt: str, deps):  # noqa: ANN001
        self.prompts.append(prompt)
        assert self.outputs, "No queued outputs left for fake agent"
        return _FakeAgentResult(self.outputs.pop(0))


@pytest.mark.asyncio
async def test_problem_set_invalid_llm_output_uses_template_fallback_when_saving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "invalid-fallback.db")
    await store.init()

    invalid_pack = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="구매팀은 오늘 공급업체 목록을 검토합니다.",
                choices=["review", "reviews", "reviewed", "reviewing"],
                answer="review",
                explanation="설명은 한국어입니다.",
                skill_tags=["toeic", "part5"],
            ),
            QuizItem(
                prompt="이 문항도 한국어로 되어 있습니다.",
                choices=["a", "b", "c", "d"],
                answer="a",
                explanation="설명은 한국어입니다.",
                skill_tags=["toeic", "part5"],
            ),
            QuizItem(
                prompt="세 번째 문항도 영어 규칙을 어깁니다.",
                choices=["a", "b", "c", "d"],
                answer="a",
                explanation="설명은 한국어입니다.",
                skill_tags=["toeic", "part5"],
            ),
        ],
    )
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: _FakeAgent(output=invalid_pack))

    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part5": 1},
    )
    result = await process_job(store=store, model="fake-model", job=job)

    ready_pack = await store.get_ready_pack("u1", result["created_pack_ids"][0])
    assert ready_pack is not None
    assert ready_pack.pack.title == "Part 5 핵심 문법 10선"
    assert ready_pack.generation is not None
    assert ready_pack.generation.strategy == "llm_invalid_fallback"
    assert "item_0_prompt_not_english" in ready_pack.generation.validation_errors
    candidate_preview = ready_pack.generation.model_extra.get("candidate_preview")
    assert candidate_preview is not None
    assert candidate_preview["item_count"] == 3
    assert candidate_preview["items"][0]["prompt"] == "구매팀은 오늘 공급업체 목록을 검토합니다."
    assert candidate_preview["items"][0]["answer"] == "review"
    assert len(ready_pack.pack.items) == 10
    assert ready_pack.pack.items[0].prompt != build_seed_ready_pack(
        topic="seed",
        mode="toeic",
        difficulty="easy",
    ).items[0].prompt
    inventory = await store.problem_inventory("u1")
    assert inventory.practice_items[0].source == "seed"
    practice_detail = await store.get_practice_item("u1", inventory.practice_items[0].item_id)
    assert practice_detail is not None
    expected_seed_item = build_part5_practice_item(0, "easy")
    assert practice_detail.item.question_text == expected_seed_item.question_text
    assert practice_detail.item.grammar_tag == expected_seed_item.grammar_tag


@pytest.mark.asyncio
async def test_problem_set_llm_error_uses_template_fallback_when_saving(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "error-fallback.db")
    await store.init()

    monkeypatch.setattr(
        jobs_module,
        "build_quiz_agent",
        lambda model: _FakeAgent(error=RuntimeError("synthetic llm failure")),
    )

    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part2": 1},
    )
    result = await process_job(store=store, model="fake-model", job=job)

    ready_pack = await store.get_ready_pack("u1", result["created_pack_ids"][0])
    assert ready_pack is not None
    assert ready_pack.pack.title == "Part 2 응답 패턴 훈련"
    assert ready_pack.generation is not None
    assert ready_pack.generation.strategy == "llm_error_fallback"
    assert ready_pack.generation.error == "synthetic llm failure"
    assert ready_pack.generation.model_extra.get("candidate_preview") is None
    assert len(ready_pack.pack.items) == 10
    assert ready_pack.pack.items[0].prompt == "Where is the orientation schedule posted?"


@pytest.mark.asyncio
async def test_problem_set_valid_llm_output_uses_pack_derived_practice_item(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "valid-llm-practice.db")
    await store.init()

    valid_pack = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="The office manager will ___ the revised seating chart this afternoon.",
                choices=["review", "reviews", "reviewed", "reviewing"],
                answer="review",
                explanation="'will' 뒤에는 동사원형이 와야 하므로 'review'가 정답입니다.",
                skill_tags=["toeic", "part5", "grammar"],
            ),
            QuizItem(
                prompt="All applicants must submit identification ___ the interview begins.",
                choices=["before", "during", "among", "unless"],
                answer="before",
                explanation="면접 시작 이전 시점을 나타내므로 'before'가 자연스럽습니다.",
                skill_tags=["toeic", "part5", "preposition"],
            ),
            QuizItem(
                prompt="The report was written so ___ that the client approved it immediately.",
                choices=["clearly", "clear", "clearness", "cleared"],
                answer="clearly",
                explanation="동사 was written을 수식하는 부사가 필요하므로 'clearly'가 맞습니다.",
                skill_tags=["toeic", "part5", "adverb"],
            ),
        ],
    )
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: _FakeAgent(output=valid_pack))

    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part5": 1},
    )
    result = await process_job(store=store, model="fake-model", job=job)

    ready_pack = await store.get_ready_pack("u1", result["created_pack_ids"][0])
    assert ready_pack is not None
    assert ready_pack.generation is not None
    assert ready_pack.generation.strategy == "llm"

    inventory = await store.problem_inventory("u1")
    assert inventory.practice_items[0].source == "worker_generated"
    practice_detail = await store.get_practice_item("u1", inventory.practice_items[0].item_id)
    assert practice_detail is not None
    assert practice_detail.item.question_text == valid_pack.items[0].prompt
    assert practice_detail.item.correct_option == valid_pack.items[0].answer
    assert practice_detail.item.grammar_tag == "worker_generated_part5"


@pytest.mark.asyncio
async def test_problem_set_normalizes_label_style_answers_before_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "normalized-answer.db")
    await store.init()

    label_answer_pack = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="The office manager will ___ the revised seating chart this afternoon.",
                choices=["review", "reviews", "reviewed", "reviewing"],
                answer="(A)",
                explanation="'will' 뒤에는 동사원형이 와야 하므로 'review'가 정답입니다.",
                skill_tags=["toeic", "part5", "grammar"],
            ),
            QuizItem(
                prompt="All applicants must submit identification ___ the interview begins.",
                choices=["before", "during", "among", "unless"],
                answer="A.",
                explanation="면접 시작 이전 시점을 나타내므로 'before'가 자연스럽습니다.",
                skill_tags=["toeic", "part5", "preposition"],
            ),
            QuizItem(
                prompt="The report was written so ___ that the client approved it immediately.",
                choices=["clearly", "clear", "clearness", "cleared"],
                answer="A",
                explanation="동사 was written을 수식하는 부사가 필요하므로 'clearly'가 맞습니다.",
                skill_tags=["toeic", "part5", "adverb"],
            ),
        ],
    )
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: _FakeAgent(output=label_answer_pack))

    job = await enqueue_problem_generation_job(
        store,
        user_id="u1",
        part_counts={"part5": 1},
    )
    result = await process_job(store=store, model="fake-model", job=job)

    ready_pack = await store.get_ready_pack("u1", result["created_pack_ids"][0])
    assert ready_pack is not None
    assert ready_pack.generation is not None
    assert ready_pack.generation.strategy == "llm"
    assert ready_pack.generation.validation_errors == []
    assert ready_pack.pack.items[0].answer == "review"
    assert ready_pack.pack.items[1].answer == "before"
    assert ready_pack.pack.items[2].answer == "clearly"


def test_template_fallback_packs_are_part_aware_and_valid():
    part2_pack = build_pack_from_template(
        {"title": "Part 2 응답 패턴 훈련", "difficulty": "easy", "item_count": 10},
        "part2",
        1,
    )
    part5_pack = build_pack_from_template(
        {"title": "Part 5 핵심 문법 10선", "difficulty": "easy", "item_count": 10},
        "part5",
        1,
    )
    part7_pack = build_pack_from_template(
        {"title": "Part 7 독해 지문 분석", "difficulty": "medium", "item_count": 20},
        "part7",
        1,
    )

    assert part2_pack.items[0].prompt == "Where is the orientation schedule posted?"
    assert "Question: What should employees do before Thursday evening?" in part7_pack.items[0].prompt
    assert "___" in part5_pack.items[0].prompt

    for pack in [part2_pack, part5_pack, part7_pack]:
        assert validate_quiz_pack(
            pack,
            require_english_items=True,
            require_korean_explanations=True,
        ) == []
        assert validate_generated_pack(
            pack,
            require_english_items=True,
            require_korean_explanations=True,
        )["passed"] is True


def test_split_generation_counts_uses_5_item_chunks():
    assert split_generation_counts(4) == [4]
    assert split_generation_counts(5) == [5]
    assert split_generation_counts(12) == [5, 5, 2]
    assert split_generation_counts(20) == [5, 5, 5, 5]


def test_toeic_ready_pack_prompt_contracts_are_part_specific():
    part2_prompt = build_toeic_ready_pack_prompt(
        topic="Part 2 응답 패턴 훈련",
        difficulty="easy",
        item_count=10,
        part_type="part2",
    )
    part3_prompt = build_toeic_ready_pack_prompt(
        topic="PART3 실전 팩 1",
        difficulty="medium",
        item_count=20,
        part_type="part3",
    )
    part5_prompt = build_toeic_ready_pack_prompt(
        topic="Part 5 핵심 문법 10선",
        difficulty="easy",
        item_count=10,
        part_type="part5",
    )
    part6_prompt = build_toeic_ready_pack_prompt(
        topic="PART6 실전 팩 1",
        difficulty="medium",
        item_count=20,
        part_type="part6",
    )
    part7_prompt = build_toeic_ready_pack_prompt(
        topic="Part 7 독해 지문 분석",
        difficulty="medium",
        item_count=20,
        part_type="part7",
    )

    assert "one-question one-response TOEIC listening response item" in part2_prompt
    assert "The prompt must be a natural question." in part2_prompt

    assert "short workplace dialogue followed by one comprehension question" in part3_prompt

    assert "single incomplete sentence with one blank shown as ___" in part5_prompt
    assert "The 4 choices must be short word or phrase options" in part5_prompt

    assert "Do not emit comma-joined choice strings." in part6_prompt
    assert "short sentence-completion grammar or vocabulary question in passage style" in part6_prompt

    assert "short reading passage such as an email, notice, memo, or article excerpt" in part7_prompt
    assert "Do not return fewer items than requested." in part7_prompt


def test_part6_post_process_splits_malformed_choice_blob_and_normalizes_answer():
    malformed_pack = QuizPack(
        title="PART6 실전 팩 1",
        mode="toeic",
        difficulty="medium",
        items=[
            QuizItem(
                prompt="All staff members ___ the mandatory safety workshop yesterday.",
                choices=["attend,\nattending,\nattended,\nattendant],explanation:"],
                answer="attended",
                explanation="문장에 'yesterday'가 있으므로 과거 시제 attended가 적절합니다.",
                skill_tags=["toeic", "part6"],
            )
        ],
    )

    normalized_pack = normalize_pack_answers(malformed_pack, part_type="part6")
    normalized_item = normalized_pack.items[0]

    assert normalized_item.choices == ["attend", "attending", "attended", "attendant"]
    assert normalized_item.answer == "attended"


def test_part6_post_process_stops_before_prompt_and_skill_tag_leakage():
    malformed_pack = QuizPack(
        title="PART6 실전 팩 1",
        mode="toeic",
        difficulty="medium",
        items=[
            QuizItem(
                prompt="Please submit ___ report by the end of the day.",
                choices=["you,\nyour,\nyours,\nyourself],explanation:\nprompt:\nPlease submit ___ report by the end of the day.\nskill_tags:[\npronoun"],
                answer="your",
                explanation="빈칸 뒤 명사를 수식하므로 소유격 your가 필요합니다.",
                skill_tags=["toeic", "part6"],
            )
        ],
    )

    normalized_pack = normalize_pack_answers(malformed_pack, part_type="part6")
    normalized_item = normalized_pack.items[0]

    assert normalized_item.choices == ["you", "your", "yours", "yourself"]
    assert normalized_item.answer == "your"


def test_part7_post_process_trims_extra_choice_and_preserves_answer():
    malformed_pack = QuizPack(
        title="Part 7 독해 지문 분석",
        mode="toeic",
        difficulty="medium",
        items=[
            QuizItem(
                prompt="What is the purpose of the email?",
                choices=[
                    "To update employees on a policy change",
                    "To announce a new product launch",
                    "To schedule a team meeting",
                    "To request feedback on a project",
                    "None of the above",
                ],
                answer="To update employees on a policy change",
                explanation="이메일의 목적은 정책 변경 공지입니다.",
                skill_tags=["toeic", "part7"],
            )
        ],
    )

    normalized_pack = normalize_pack_answers(malformed_pack, part_type="part7")
    normalized_item = normalized_pack.items[0]

    assert normalized_item.choices == [
        "To update employees on a policy change",
        "To announce a new product launch",
        "To schedule a team meeting",
        "To request feedback on a project",
    ]
    assert normalized_item.answer == "To update employees on a policy change"


def test_part2_post_process_removes_none_of_the_above_choice():
    malformed_pack = QuizPack(
        title="Part 2 응답 패턴 훈련",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="Where is the meeting being held?",
                choices=[
                    "It's in the conference room.",
                    "At ten o'clock.",
                    "Yes, it is.",
                    "By email.",
                    "(E) None of the above.",
                ],
                answer="It's in the conference room.",
                explanation="장소 질문이므로 회의실 응답이 정답입니다.",
                skill_tags=["toeic", "part2"],
            )
        ],
    )

    normalized_pack = normalize_pack_answers(malformed_pack, part_type="part2")
    normalized_item = normalized_pack.items[0]

    assert normalized_item.choices == [
        "It's in the conference room.",
        "At ten o'clock.",
        "Yes, it is.",
        "By email.",
    ]
    assert normalized_item.answer == "It's in the conference room."


@pytest.mark.asyncio
async def test_generate_ready_pack_repairs_invalid_chunk_once_before_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "repair-success.db")
    await store.init()

    invalid_chunk = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="Where is the meeting being held?",
                choices=["It's in the conference room.", "At ten o'clock.", "Yes, it is."],
                answer="It's in the conference room.",
                explanation="장소 질문이므로 회의실 응답이 맞습니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="When will the manager arrive?",
                choices=["Tomorrow morning.", "At the station.", "Yes, he does.", "By bus."],
                answer="Tomorrow morning.",
                explanation="시간을 묻는 질문입니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="Who approved the revised budget?",
                choices=["The finance director.", "Tomorrow afternoon.", "In the lobby.", "By courier."],
                answer="The finance director.",
                explanation="사람을 묻는 질문입니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="Why was the shipment delayed?",
                choices=["Because of heavy traffic.", "At the warehouse.", "Yes, it was.", "By noon."],
                answer="Because of heavy traffic.",
                explanation="이유를 묻는 질문입니다.",
                skill_tags=["toeic", "part2"],
            ),
        ],
    )
    repaired_chunk = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="Where is the meeting being held?",
                choices=["It's in the conference room.", "At ten o'clock.", "Yes, it is.", "By email."],
                answer="It's in the conference room.",
                explanation="장소 질문이므로 회의실 응답이 맞습니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="When will the manager arrive?",
                choices=["Tomorrow morning.", "At the station.", "Yes, he does.", "By bus."],
                answer="Tomorrow morning.",
                explanation="시간을 묻는 질문이므로 시간 응답이 정답입니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="Who approved the revised budget?",
                choices=["The finance director.", "Tomorrow afternoon.", "In the lobby.", "By courier."],
                answer="The finance director.",
                explanation="사람을 묻는 질문이므로 사람 응답이 정답입니다.",
                skill_tags=["toeic", "part2"],
            ),
            QuizItem(
                prompt="Why was the shipment delayed?",
                choices=["Because of heavy traffic.", "At the warehouse.", "Yes, it was.", "By noon."],
                answer="Because of heavy traffic.",
                explanation="이유를 묻는 질문이므로 원인 응답이 정답입니다.",
                skill_tags=["toeic", "part2"],
            ),
        ],
    )
    fake_agent = _QueuedFakeAgent([invalid_chunk, repaired_chunk])
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: fake_agent)

    pack, generation_meta = await generate_ready_pack(
        store=store,
        model="fake-model",
        user_id="u1",
        topic="Part 2 응답 패턴 훈련",
        mode="toeic",
        difficulty="easy",
        item_count=4,
        part_type="part2",
    )

    assert generation_meta["strategy"] == "llm_repair"
    assert generation_meta["repair_attempted"] is True
    assert generation_meta["repair_success_count"] == 1
    assert len(pack.items) == 4
    assert "Repair pass" in fake_agent.prompts[1]


@pytest.mark.asyncio
async def test_generate_ready_pack_falls_back_after_failed_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "repair-fallback.db")
    await store.init()

    invalid_chunk = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="Where is the meeting being held?",
                choices=["It's in the conference room.", "At ten o'clock.", "Yes, it is."],
                answer="It's in the conference room.",
                explanation="장소 질문이므로 회의실 응답이 맞습니다.",
                skill_tags=["toeic", "part2"],
            ),
        ],
    )
    still_invalid_chunk = QuizPack(
        title="ignored",
        mode="toeic",
        difficulty="easy",
        items=[
            QuizItem(
                prompt="Where is the meeting being held?",
                choices=["It's in the conference room.", "At ten o'clock.", "Yes, it is."],
                answer="It's in the conference room.",
                explanation="장소 질문이므로 회의실 응답이 맞습니다.",
                skill_tags=["toeic", "part2"],
            ),
        ],
    )
    fake_agent = _QueuedFakeAgent([invalid_chunk, still_invalid_chunk])
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: fake_agent)

    pack, generation_meta = await generate_ready_pack(
        store=store,
        model="fake-model",
        user_id="u1",
        topic="Part 2 응답 패턴 훈련",
        mode="toeic",
        difficulty="easy",
        item_count=1,
        part_type="part2",
    )

    assert generation_meta["strategy"] == "llm_invalid_fallback"
    assert generation_meta["repair_attempted"] is True
    assert generation_meta["failed_chunk_index"] == 1
    assert generation_meta["candidate_preview"]["item_count"] == 1
    assert generation_meta["repair_candidate_preview"]["item_count"] == 1
    assert pack.title == "Part 2 응답 패턴 훈련"


@pytest.mark.asyncio
async def test_generate_ready_pack_splits_large_toeic_requests_into_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = SqliteStore(tmp_path / "chunked-ready-pack.db")
    await store.init()

    fake_agent = _ChunkedFakeAgent()
    monkeypatch.setattr(jobs_module, "build_quiz_agent", lambda model: fake_agent)

    pack, generation_meta = await generate_ready_pack(
        store=store,
        model="fake-model",
        user_id="u1",
        topic="Part 7 독해 지문 분석",
        mode="toeic",
        difficulty="medium",
        item_count=12,
        part_type="part7",
    )

    assert generation_meta["strategy"] == "llm"
    assert generation_meta["chunk_count"] == 3
    assert generation_meta["requested_item_count"] == 12
    assert len(pack.items) == 12
    assert len(fake_agent.prompts) == 3
    assert "chunk 1 of 3" in fake_agent.prompts[0]
    assert "chunk 2 of 3" in fake_agent.prompts[1]
    assert "chunk 3 of 3" in fake_agent.prompts[2]
