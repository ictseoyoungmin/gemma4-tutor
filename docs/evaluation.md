# Evaluation Plan

## Goals

1. detect regressions when switching from Gemini API to `llama.cpp`
2. verify structured outputs remain valid
3. verify required routes stay responsive
4. measure latency and contract compliance

## Harness layers

### 1. Schema harness
- response contains required top-level keys
- structured outputs validate as Pydantic models

### 2. Tool-routing harness
Planned extension:
- assert that memory retrieval happens in personalization scenarios
- assert that quiz generation stays in quiz agent path

### 3. Behavior harness
Planned extension:
- education tone scoring
- grounding scoring
- difficulty-match scoring

### 4. Performance harness
- end-to-end latency for chat and quiz generation
- separate thresholds for API backend vs local backend

## Suggested benchmark matrix

| Scenario | Backend | Target |
|---|---|---|
| chat personalization | Gemini API | rapid iteration quality |
| grammar quiz generation | Gemini API | prompt design |
| chat personalization | llama.cpp | system contract + latency |
| image analysis | llama.cpp | multimodal local path |

## Nightly plan

- smoke test against running `llama-server`
- run a small golden set
- persist JSON report artifact
