from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MemoryItem(BaseModel):
    memory_id: str = Field(default_factory=lambda: uuid4().hex)
    category: Literal["fact", "preference", "weakness", "strength", "milestone"]
    content: str
    confidence: float = 0.7
    created_at: datetime = Field(default_factory=utcnow)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str | None = None
    message: str
    model_name: str | None = None


class TutorResponse(BaseModel):
    message: str
    detected_intent: Literal[
        "chat", "quiz_request", "analysis", "memory_update", "image_learning"
    ] = "chat"
    memory_to_store: list[MemoryItem] = Field(default_factory=list)
    suggested_next_actions: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    run_id: str
    output: TutorResponse
    usage: dict[str, Any] = Field(default_factory=dict)


class QuizItem(BaseModel):
    prompt: str
    choices: list[str] = Field(default_factory=list)
    answer: str
    explanation: str
    skill_tags: list[str] = Field(default_factory=list)


class QuizPack(BaseModel):
    title: str
    mode: Literal["toeic", "grammar", "conversation", "image", "idiom"]
    difficulty: Literal["easy", "medium", "hard"]
    items: list[QuizItem]


class QuizGenerateRequest(BaseModel):
    user_id: str
    topic: str
    mode: Literal["toeic", "grammar", "conversation", "image", "idiom"] = "grammar"
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    count: int = 3


class QuizGenerateResponse(BaseModel):
    quiz_id: str
    pack: QuizPack


class QuizSubmitRequest(BaseModel):
    user_id: str
    quiz_id: str
    answers: list[str]


class QuizSubmitResponse(BaseModel):
    quiz_id: str
    total: int
    correct: int
    feedback: list[str]
    score: float


class ToeicPracticeItem(BaseModel):
    item_id: str
    part_type: Literal["part1", "part2", "part3", "part4", "part5", "part6", "part7"]
    difficulty_level: Literal["easy", "medium", "hard"]
    question_text: str
    prompt: str
    options: list[str] = Field(min_length=4, max_length=4)
    correct_option: str
    explanation: str
    grammar_tag: str
    vocab_tag: str | None = None
    validated: bool = True
    validation_score: float = 1.0


class ToeicNextRequest(BaseModel):
    user_id: str
    part_type: Literal["part5"] = "part5"


class ToeicNextResponse(BaseModel):
    item: ToeicPracticeItem
    recommended_difficulty: Literal["easy", "medium", "hard"]
    weak_tags: list[str] = Field(default_factory=list)
    recent_accuracy: float = 0.0


class ToeicAnswerRequest(BaseModel):
    user_id: str
    item_id: str
    selected_option: str
    response_time_ms: int = Field(default=0, ge=0)


class ToeicAnswerResponse(BaseModel):
    item_id: str
    correct: bool
    correct_option: str
    explanation: str
    grammar_tag: str
    vocab_tag: str | None = None
    weak_tags: list[str] = Field(default_factory=list)
    recommended_difficulty: Literal["easy", "medium", "hard"]
    recent_accuracy: float = 0.0


class PracticeItemSummary(BaseModel):
    item_id: str
    part_type: Literal["part1", "part2", "part3", "part4", "part5", "part6", "part7"]
    difficulty_level: Literal["easy", "medium", "hard"]
    prompt: str
    grammar_tag: str
    vocab_tag: str | None = None
    source: Literal["seed", "worker_generated"] = "seed"
    created_at: datetime = Field(default_factory=utcnow)


class ImageAnalysisResponse(BaseModel):
    scene_summary: str
    vocabulary: list[str] = Field(default_factory=list)
    suggested_question_types: list[str] = Field(default_factory=list)
    generated_prompt_seed: str


class SkillSnapshot(BaseModel):
    skill_name: str
    score: float
    delta: float = 0.0
    evidence_count: int = 0


class AchievementCard(BaseModel):
    achievement_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    description: str
    unlocked: bool = False
    unlocked_at: datetime | None = None


class BackgroundJob(BaseModel):
    job_id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str
    job_type: Literal["prebuild_quiz", "generate_problem_set", "summarize_session", "refresh_dashboard", "placeholder"]
    status: Literal["queued", "running", "done", "failed"] = "queued"
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class QueueJobRequest(BaseModel):
    user_id: str
    job_type: Literal["prebuild_quiz", "generate_problem_set", "summarize_session", "refresh_dashboard", "placeholder"]
    payload: dict[str, Any] = Field(default_factory=dict)


class QueueJobResponse(BaseModel):
    job: BackgroundJob


class WorkerStartRequest(BaseModel):
    poll_interval: float = 2.0
    max_jobs: int | None = None


class WorkerStatusResponse(BaseModel):
    state: Literal["running", "stopped"]
    pid: int | None = None
    poll_interval: float | None = None
    max_jobs: int | None = None
    last_exit_code: int | None = None


class HarnessCaseResult(BaseModel):
    case_id: str
    status_code: int
    elapsed_ms: float
    passed: bool
    body_preview: str


class HarnessRunRequest(BaseModel):
    mode: Literal["asgi", "http"] = "asgi"
    base_url: str = "http://127.0.0.1:8000"


class HarnessRunResponse(BaseModel):
    passed: int
    total: int
    results: list[HarnessCaseResult] = Field(default_factory=list)


class ProblemGenerationRequest(BaseModel):
    user_id: str
    part1: int = Field(default=0, ge=0, le=20)
    part2: int = Field(default=0, ge=0, le=20)
    part3: int = Field(default=0, ge=0, le=20)
    part4: int = Field(default=0, ge=0, le=20)
    part5: int = Field(default=0, ge=0, le=20)
    part6: int = Field(default=0, ge=0, le=20)
    part7: int = Field(default=0, ge=0, le=20)


class ProblemGenerationResponse(BaseModel):
    queued_job: BackgroundJob
    requested_pack_count: int


class ProblemStats(BaseModel):
    total_ready_packs: int = 0
    total_practice_items: int = 0
    practice_items_by_part: dict[str, int] = Field(default_factory=dict)
    ready_packs_by_mode: dict[str, int] = Field(default_factory=dict)


class PackGenerationMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    strategy: str = "seed_fallback"
    validated: bool = False
    validation_errors: list[str] = Field(default_factory=list)
    harness: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class ProblemInventoryResponse(BaseModel):
    stats: ProblemStats
    ready_packs: list[ReadyQuizSummary] = Field(default_factory=list)
    practice_items: list[PracticeItemSummary] = Field(default_factory=list)
    active_jobs: list[BackgroundJob] = Field(default_factory=list)
    ready_pack_page: int = 1
    practice_item_page: int = 1
    page_size: int = 5


class DeleteResourceResponse(BaseModel):
    deleted: bool
    resource_id: str


class ReadyQuizSummary(BaseModel):
    ready_pack_id: str
    title: str
    mode: Literal["toeic", "grammar", "conversation", "image", "idiom"]
    difficulty: Literal["easy", "medium", "hard"]
    generation: PackGenerationMeta | None = None
    created_at: datetime = Field(default_factory=utcnow)


class ReadyPackDetail(BaseModel):
    ready_pack_id: str
    pack: QuizPack
    generation: PackGenerationMeta | None = None


class PracticeItemDetail(BaseModel):
    item: ToeicPracticeItem
    source: Literal["seed", "worker_generated"] = "seed"
    created_at: datetime = Field(default_factory=utcnow)


class ReadyPackLaunchRequest(BaseModel):
    user_id: str


class ReadyPackLaunchResponse(BaseModel):
    ready_pack_id: str
    quiz_id: str
    pack: QuizPack


class DashboardOverview(BaseModel):
    user_id: str
    memory_count: int
    quiz_count: int
    attempts_count: int
    average_score: float


class DashboardDetail(BaseModel):
    overview: DashboardOverview
    skill_snapshots: list[SkillSnapshot] = Field(default_factory=list)
    achievements: list[AchievementCard] = Field(default_factory=list)
    ready_packs: list[ReadyQuizSummary] = Field(default_factory=list)
    active_jobs: list[BackgroundJob] = Field(default_factory=list)
    roadmap_placeholders: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    backend: str
    model_name: str
