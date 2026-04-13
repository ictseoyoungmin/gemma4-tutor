from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


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
    part_type: Literal["part5"]
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
    job_type: Literal["prebuild_quiz", "summarize_session", "refresh_dashboard", "placeholder"]
    status: Literal["queued", "running", "done", "failed"] = "queued"
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class QueueJobRequest(BaseModel):
    user_id: str
    job_type: Literal["prebuild_quiz", "summarize_session", "refresh_dashboard", "placeholder"]
    payload: dict[str, Any] = Field(default_factory=dict)


class QueueJobResponse(BaseModel):
    job: BackgroundJob


class ReadyQuizSummary(BaseModel):
    ready_pack_id: str
    title: str
    mode: Literal["toeic", "grammar", "conversation", "image", "idiom"]
    difficulty: Literal["easy", "medium", "hard"]
    created_at: datetime = Field(default_factory=utcnow)


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
