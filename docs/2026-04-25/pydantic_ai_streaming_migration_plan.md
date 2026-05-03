# 2026-04-25 Pydantic-AI Streaming Migration Plan

## Context

The minimal project at `minimal/llama_pydantic_vite_stream_minimal` proves that local `llama.cpp` can stream through `pydantic-ai` with visible answer deltas and reasoning deltas.

The current main app moved local Gemma chat to a raw `llama.cpp` stream because the original `pydantic-ai` route felt blocked until structured output was ready. That raw path restored speed, but it also forced us to reimplement pieces that `pydantic-ai` normally gives us:

- structured output parsing
- session history format
- tool orchestration
- cleaner intent/suggestion contracts

The new goal is to port the minimal project's event-streaming technique into the main app and make the local streaming backend switchable.

## Minimal Project Technique

The working minimal implementation uses these specific techniques:

- `Agent(..., output_type=str)` instead of a structured output model.
- `agent.run_stream_events(...)`, not `result.stream_output(...)`.
- Event-level parsing:
  - `AgentRunResultEvent` for final completion.
  - `PartStartEvent` for initial part text.
  - `PartDeltaEvent` for incremental deltas.
- Delta classification:
  - `ThinkingPartDelta` means reasoning.
  - `TextPartDelta` means answer text.
  - fallback classification through class name inspection.
- Text extraction from multiple possible attributes:
  - `content_delta`
  - `content`
  - `text`
  - `value`
- Local model settings:
  - `thinking`
  - `extra_body.chat_template_kwargs.enable_thinking`
  - `extra_body.reasoning_format`
- NDJSON transport:
  - `reasoning_delta`
  - `answer_delta`
  - `done`
  - `error`
- Metrics are collected independently from model output so UI can update while streaming.

The important architectural point: the minimal pydantic path streams plain text first and does not force structured output during the stream.

## Current Main-App Difference

The main app's older pydantic route used:

- `Agent(..., output_type=TutorResponse)`
- tool definitions
- session history as pydantic-ai model messages
- `result.stream_output(...)`

That combination is much heavier than the minimal app:

- structured output may delay visible answer text
- tool declarations increase prompt size
- local Gemma may spend more time satisfying schema/tool constraints
- reasoning and answer deltas are harder to expose early

The raw route fixed this by bypassing pydantic-ai, but now we have duplicated parsing and metadata logic.

## Proposed Switching Design

Add a local chat streaming mode setting:

```env
LLAMA_CHAT_STREAM_MODE=raw
```

Allowed values:

- `raw`
  - current raw `llama.cpp` SSE path
  - fastest and lowest-level
  - keeps `<ui_json>` hidden metadata parsing
- `pydantic_text`
  - new pydantic-ai path based on the minimal project
  - `output_type=str`
  - `run_stream_events()`
  - answer/reasoning deltas exposed directly
  - final text is converted into `TutorResponse`
- `pydantic_agent`
  - existing heavier structured agent path
  - keeps tools and `TutorResponse` structured output
  - useful for debugging or hosted-style parity

Recommended default during migration:

```env
LLAMA_CHAT_STREAM_MODE=raw
```

Then test `pydantic_text` locally. If latency and quality are good, promote `pydantic_text` to the default.

## Patch Plan

### 1. Configuration

Add to `Settings`:

```python
llama_chat_stream_mode: Literal["raw", "pydantic_text", "pydantic_agent"] = "raw"
```

Document it in `.env.compose.example` and README.

### 2. Reusable Pydantic Stream Helpers

Port these helpers from the minimal project into main app code:

- `_extract_field()`
- `_class_name()`
- `_part_kind()`
- `_extract_content()`
- `StreamMetrics` or a smaller equivalent

Import with version tolerance:

```python
try:
    from pydantic_ai import TextPartDelta, ThinkingPartDelta
except Exception:
    TextPartDelta = None
    ThinkingPartDelta = None
```

### 3. Lightweight Local Agent

Create a new local streaming agent factory:

```python
def build_local_text_stream_agent(model) -> Agent[TutorDeps, str]:
    return Agent(
        model,
        deps_type=TutorDeps,
        output_type=str,
        system_prompt=LOCAL_TUTOR_SYSTEM_PROMPT + metadata instructions,
    )
```

Do not attach tools in the first patch. Keep it close to the minimal project.

### 4. Pydantic Text Stream Function

Add a new backend function:

```python
async def _build_pydantic_text_llama_chat_stream(...):
```

Behavior:

- resolve session id like the current route
- load short raw history or pydantic history only if it is compatible
- include recent memories in the system prompt
- call `agent.run_stream_events(...)`
- emit current app NDJSON event names:
  - `metadata`
  - `metrics`
  - `reasoning_delta`
  - `message_delta`
  - `final`
  - `error`
- run the same `<ui_json>` hidden metadata parser used by the raw path
- build the final `ChatResponse`

### 5. Router Switch

In `build_chat_stream()`:

```python
if selected_backend == "llama_cpp":
    if settings.llama_chat_stream_mode == "raw":
        return _build_raw_llama_chat_stream(...)
    if settings.llama_chat_stream_mode == "pydantic_text":
        return _build_pydantic_text_llama_chat_stream(...)
    return _build_structured_agent_chat_stream(...)
```

The frontend should not need a route change.

### 6. Tool Routing Reintroduction

Do not add tools to `pydantic_text` immediately.

After the stream path is validated:

1. Add a small set of read-only tools.
2. Measure first-token latency.
3. Add memory write only if it does not hurt latency too much.
4. Keep `pydantic_agent` as the full orchestration path for comparison.

### 7. Tests

Add focused tests for:

- setting validation for `LLAMA_CHAT_STREAM_MODE`
- pydantic event delta classification
- hidden `<ui_json>` parsing shared by raw and pydantic text stream
- mode switch dispatch in `build_chat_stream()`
- malformed metadata fallback

### 8. Smoke Workflow

Add smoke commands that run all local stream modes:

- raw reasoning off
- raw reasoning on
- pydantic text reasoning off
- pydantic text reasoning on

Record:

- first visible answer time
- first reasoning time
- total time
- whether suggestions parsed
- whether `<ui_json>` leaked

## Risks

- `pydantic_text` may still be slower than raw if pydantic-ai emits events only after internal buffering for this model/template.
- `ThinkingPartDelta` availability may depend on installed `pydantic-ai` version.
- Tool reintroduction can quickly recreate the original latency problem.
- Mixing raw history and pydantic message history needs careful conversion.

## Decision Criteria

Promote `pydantic_text` over `raw` only if:

- answer deltas appear quickly enough in the current app
- reasoning deltas are visible when reasoning is enabled
- suggestions can still be parsed through hidden metadata
- local multiturn behavior remains acceptable
- first-token latency is close to raw mode for common learner prompts

Otherwise keep raw as default and use `pydantic_text` as an experimental mode.
