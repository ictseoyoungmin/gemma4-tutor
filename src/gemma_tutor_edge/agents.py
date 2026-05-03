from __future__ import annotations

from typing import Sequence

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import BinaryContent

from .deps import ContentDeps, TutorDeps
from .schemas import ImageAnalysisResponse, MemoryItem, QuizPack, TutorResponse


TUTOR_SYSTEM_PROMPT = """
You are Gemma Tutor Edge, a patient and practical English tutor.
Your goals:
- help the learner improve English in a low-cost, local-first study workflow
- reference the learner's recent history when useful
- prefer actionable feedback over vague praise
- suggest the next best study action when appropriate
- when something is worth remembering, return it in memory_to_store
""".strip()


LOCAL_TUTOR_SYSTEM_PROMPT = (
    "You are Gemma Tutor Edge, a practical English tutor. "
    "Reply in Korean unless the learner asks for English. "
    "Keep answers short, concrete, and directly useful for TOEIC or English study. "
    "- CRITICAL: Verify the grammatical correctness of the answer before responding. "
    "- If a question is flawed or has a typo, point it out instead of providing a wrong explanation. "
    "- Ensure 'plan' is explained as 'plan + to + verb' in TOEIC contexts. "
    "- explanations should teach, not only reveal the answer"
    "- output must be fully structured"
    "Use '_' to indicate blanks in questions created at the user's request."
    "If the learner asks for a tip, provide one specific tip with a short example or next action. "
    "Suggested next actions must be short button labels, ideally 2 to 5 Korean words. "
    "Do not put full sentences in suggested_next_actions. "
    "Keep private reasoning out of the final message field. "
    "Use tools when they help personalize or route the next study step. "
    "Keep learner-facing explanation separate from UI metadata."
    "Suggestion text must never appear in answer body; only inside <ui_json>"
)


QUIZ_SYSTEM_PROMPT = """
You generate compact, high-quality English learning quiz packs.
Constraints:
- keep prompts concise
- explanations should teach, not only reveal the answer
- difficulty should match the request
- output must be fully structured
""".strip()


VISION_SYSTEM_PROMPT = """
You analyze a learner-provided image and transform it into English learning material.
Focus on scene description, vocabulary extraction, and question-generation seeds.
""".strip()


def _build_tutor_agent(model, *, system_prompt: str) -> Agent[TutorDeps, TutorResponse]:
    agent: Agent[TutorDeps, TutorResponse] = Agent(
        model,
        deps_type=TutorDeps,
        output_type=TutorResponse,
        system_prompt=system_prompt,
        tool_timeout=120,
    )

    @agent.tool
    async def get_recent_memories(ctx: RunContext[TutorDeps], limit: int = 5) -> list[MemoryItem]:
        """Fetch recent learner memories for personalization."""
        return await ctx.deps.store.list_recent_memories(ctx.deps.user_id, limit=limit)

    @agent.tool
    async def save_memory(
        ctx: RunContext[TutorDeps],
        category: str,
        content: str,
        confidence: float = 0.8,
    ) -> str:
        """Persist a memory item for the learner."""
        item = MemoryItem(category=category, content=content, confidence=confidence)
        await ctx.deps.store.add_memory(ctx.deps.user_id, item)
        return f"Saved memory {item.memory_id}"

    @agent.tool
    async def get_progress_summary(ctx: RunContext[TutorDeps]) -> str:
        """Return summary statistics for the learner dashboard."""
        overview = await ctx.deps.store.dashboard_overview(ctx.deps.user_id)
        return (
            f"memory_count={overview.memory_count}, quiz_count={overview.quiz_count}, "
            f"attempts_count={overview.attempts_count}, average_score={overview.average_score:.2f}"
        )

    return agent


def build_tutor_agent(model) -> Agent[TutorDeps, TutorResponse]:
    return _build_tutor_agent(model, system_prompt=TUTOR_SYSTEM_PROMPT)


def build_local_tutor_agent(model) -> Agent[TutorDeps, TutorResponse]:
    return _build_tutor_agent(
        model,
        system_prompt=LOCAL_TUTOR_SYSTEM_PROMPT,
    )


def build_quiz_agent(model) -> Agent[ContentDeps, QuizPack]:
    return Agent(
        model,
        deps_type=ContentDeps,
        output_type=QuizPack,
        system_prompt=QUIZ_SYSTEM_PROMPT,
        tool_timeout=120,
    )


def build_vision_agent(model) -> Agent[ContentDeps, ImageAnalysisResponse]:
    return Agent(
        model,
        deps_type=ContentDeps,
        output_type=ImageAnalysisResponse,
        system_prompt=VISION_SYSTEM_PROMPT,
        tool_timeout=120,
    )


async def run_image_analysis(agent: Agent[ContentDeps, ImageAnalysisResponse], prompt: str, image_bytes: bytes, media_type: str, deps: ContentDeps) -> ImageAnalysisResponse:
    result = await agent.run(
        [
            f"This is an uploaded learner image. {prompt}",
            BinaryContent(data=image_bytes, media_type=media_type),
        ],
        deps=deps,
    )
    return result.output
