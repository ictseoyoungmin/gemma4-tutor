# 2026-04-25 Local Gemma Raw Stream Structured Metadata Plan

## Problem

The local Gemma 4 chat path was moved from the `pydantic-ai` structured agent stream to a raw `llama.cpp` OpenAI-compatible stream so learner-visible tokens arrive quickly.

That fixed the major latency problem, but it introduced a structure problem:

- Gemini responses still produce reliable `TutorResponse` fields through structured output.
- Local Gemma raw streaming produces free-form text only.
- The model may write UI metadata into the learner-visible answer, for example:
  - `quiz_request`
  - `Next action: ...`
  - `[단어 테스트하기]`
- Rule-based postprocessing can extract some actions, but it is brittle and suppresses the model's ability to create high-quality, context-specific suggestions.

## Goal

Keep the fast raw local stream while restoring a structured contract for UI metadata.

The model should produce:

1. A normal learner-facing answer.
2. A hidden JSON metadata block for the UI.

Example:

```text
비즈니스 영어 어휘 3개를 골라봤습니다...

<ui_json>
{
  "detected_intent": "chat",
  "suggested_next_actions": [
    "위 단어로 문장 만들어보기",
    "다른 비즈니스 표현 더 알아보기",
    "TOEIC 파트 5 관련 비즈니스 어휘 퀴즈 풀기"
  ],
  "memory_to_store": []
}
</ui_json>
```

## Design

- Keep `/v1/chat/stream` route stable.
- For `llama_cpp`, keep using raw `/chat/completions` SSE streaming.
- Add prompt instructions requiring a final `<ui_json>...</ui_json>` block.
- Backend stream parser sends only text before `<ui_json>` as `message_delta`.
- Backend buffers the JSON block internally and never streams it to the UI.
- At stream end, backend parses the JSON block and validates it into `TutorResponse`.
- If metadata parsing fails, the learner answer still succeeds with empty suggestions.
- Remove brittle rule-based suggestion extraction for local raw output.

## Acceptance

- Local Gemma suggestions can be freely authored by the model and appear as suggestion buttons.
- `<ui_json>` and raw metadata never appear in the chat transcript.
- Fast token streaming remains intact.
- Missing or malformed metadata does not fail the chat request.
- Existing frontend contract remains unchanged.

## Implementation Steps

1. Update local raw system prompt with explicit metadata-block instructions.
2. Add a streaming split parser for `<ui_json>` boundaries.
3. Add final metadata parsing and `TutorResponse` construction.
4. Remove rule-based local suggestion inference.
5. Add focused tests for metadata extraction and malformed JSON fallback.
