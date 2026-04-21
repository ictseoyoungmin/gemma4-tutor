# 2026-04-21 Pack Generation Slice Plan

## Goal

Today focuses on the next stability step for TOEIC pack generation and operator usability.

Requested product changes:

- do not generate the full target item count in one large pass,
- generate in smaller chunks of around 4 to 5 items and merge them,
- add a repair step for invalid LLM output when feasible,
- allow model selection in the AI tutor chat UI,
- keep the work organized in small sequential slices,
- mark completed slices clearly.

## Slice Plan

### Slice 1. Chunked TOEIC pack generation

Status:

- `completed`

Scope:

- split TOEIC generation into 4 to 5 item chunk requests,
- merge chunk outputs into one Ready Pack,
- keep fallback behavior intact if chunked generation still fails,
- add regression coverage for chunk counts and merged item totals.

Completed work:

- added chunk split logic for TOEIC generation with a default chunk size of `5`,
- updated TOEIC prompt construction so each chunk call includes chunk index and per-chunk exact count,
- merged successful chunk outputs back into one Ready Pack before final validation,
- relaxed chunk-local minimum-item validation while preserving final merged-pack validation,
- added regression coverage for chunk splitting and merged total item count.

### Slice 2. Invalid-output repair pass

Status:

- `completed`

Scope:

- add one bounded repair attempt when the first LLM output is structurally invalid,
- preserve the failed original attempt preview for the UI,
- distinguish first-pass success, repair success, and fallback in metadata.

Completed work:

- added one bounded repair attempt for invalid TOEIC chunk outputs,
- introduced a structured repair prompt that reuses the part-specific contract and lists concrete validation failures,
- preserved both the original failed candidate preview and the repair-attempt preview in metadata when repair still fails,
- distinguished plain `llm` success from `llm_repair` success in generation metadata,
- added regression tests for repair success and repair-fallback behavior.

### Slice 3. Tutor chat model selector

Status:

- `completed`

Scope:

- allow choosing the tutor chat model from the learner workspace,
- pass the selected model through the API request path,
- keep a safe default if no model is selected.

Completed work:

- added per-request `model_name` support to chat requests,
- added backend model override handling for tutor chat without changing the global worker model,
- added a model selector UI to the learner workspace tutor chat panel,
- wired the selected model through the frontend API request path,
- verified the frontend build after the selector integration.

### Slice 4. Follow-up UI/operator polish

Status:

- `pending`

Scope:

- improve pack generation observability around repair/chunk runs,
- reflect slice outcomes in the `문제` tab and follow-up docs.

## Notes

- Start with chunking because `part7` and other larger packs are currently failing partly due to oversized single-pass requests.
- Keep each slice independently testable before moving to the next one.
