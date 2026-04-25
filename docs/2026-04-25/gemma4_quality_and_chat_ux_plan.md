# 2026-04-25 Gemma 4 Response Quality And Chat UX Plan

## Goal

Improve the local Gemma 4 learner chat experience, with special focus on:

- clearer streaming output while the local model is generating
- better reasoning visibility and immediate reasoning control from the chat panel
- stronger final answer quality for local Gemma 4
- lower confusion between reasoning text, final answer text, and diagnostics

This plan assumes the 2026-04-23 local `llama.cpp` Compose path is already working and treats infrastructure as baseline unless a runtime issue blocks UX or quality validation.

## Current Baseline

- `/v1/chat/stream` exists and emits NDJSON events:
  - `metadata`
  - `metrics`
  - `reasoning_delta`
  - `message_delta`
  - `final`
  - `error`
- The chat UI appends reasoning and answer deltas into an assistant placeholder turn.
- Each assistant bubble can show or hide its reasoning block.
- The local Gemma 4 runtime is exposed through `/v1/health` and the model picker.
- Local responses work end-to-end, but quality is still inconsistent:
  - occasional prompt echoing
  - generic or low-value final answers
  - possible leakage of reasoning-like text into the answer
  - long waits that need clearer progressive feedback

## Prioritized Work Slices

### Slice 1. Reasoning Control And Streaming Output Polish

Priority: `P0`

Status: `completed`

Objective:

Make reasoning behavior controllable directly from the chat panel and make streaming output easier to follow while Gemma 4 is generating.

Scope:

- Add a visible reasoning on/off icon control to the chat composer.
- Send the reasoning preference with chat requests so local `llama.cpp` can enable or disable thinking per request.
- Keep the existing per-message reasoning show/hide affordance, but make it cleaner and less text-heavy.
- Avoid duplicate loading indicators when an assistant placeholder is already streaming.
- Make the current streaming state obvious without obscuring the answer.

Acceptance:

- The user can toggle reasoning before sending a chat message.
- The request payload carries that preference to the backend.
- Local `llama_cpp` requests use the preference when building model settings.
- When reasoning is off, new local responses do not request thinking from the model.
- When reasoning is on, reasoning deltas can be shown and collapsed per message.
- The UI no longer shows an extra typing bubble in addition to the streaming assistant placeholder.

Completed work:

- Added `reasoning_enabled` to the chat request contract.
- Threaded the reasoning preference through the frontend streaming request payload.
- Added a chat composer icon button for immediate reasoning on/off control.
- Updated local `llama_cpp` model settings so per-request reasoning overrides the environment default.
- Kept per-message reasoning show/hide behavior and preserved open state when a streaming placeholder becomes the final assistant turn.
- Replaced the duplicate typing bubble during text streaming with an inline assistant placeholder state.

### Slice 2. Local Gemma 4 Prompt And Structured Output Tightening

Priority: `P0`

Status: `pending`

Objective:

Improve final answer quality from the local Gemma 4 tutor path without changing the public API contract.

Scope:

- Refine the local tutor system prompt for concise Korean tutoring answers.
- Add explicit constraints against prompt echoing and reasoning leakage.
- Encourage a short, useful final answer first, with next actions only when useful.
- Review structured output behavior with local Gemma 4 and adjust prompt wording if needed.

Acceptance:

- Local answers are shorter, more directly useful, and less likely to echo the user prompt.
- Reasoning-like planning text does not appear in `output.message`.
- The structured `TutorResponse` fields remain valid.

### Slice 3. Stream Diagnostics And Debug Visibility

Priority: `P1`

Status: `completed`

Objective:

Make performance and stream state inspectable without making the learner-facing chat feel noisy.

Scope:

- Keep first-token and total-time diagnostics available.
- Move low-level diagnostics into a compact debug affordance or metadata line.
- Ensure the status bar is readable during long local generations.
- Consider a small "generating" state inside the assistant bubble.

Acceptance:

- Developers can still see first-token and total latency.
- Learners are not distracted by raw diagnostics in normal use.
- Long-running local responses communicate progress clearly.

Completed work:

- Changed learner-visible first-token and total-time labels from millisecond values to seconds.
- Kept the live stream meter in seconds so the chat UI uses one consistent time unit.
- Moved completed-response first/total latency into a compact expandable `Stats` affordance so normal learner chat is less noisy.

### Slice 4. Image-Attachment Local Quality Pass

Priority: `P1`

Status: `pending`

Objective:

Improve the quality and usefulness of `/v1/image/analyze` responses when backed by local Gemma 4 multimodal inference.

Scope:

- Review the vision prompt for local multimodal behavior.
- Add constraints for grounded scene description and vocabulary extraction.
- Preserve the existing image-analysis response schema.
- Verify that local image responses are not generic placeholder text.

Acceptance:

- Image responses mention visible content when possible.
- Vocabulary is grounded in the uploaded image.
- Suggested question types are useful for English study.

### Slice 5. Regression Tests And Smoke Workflow Refresh

Priority: `P2`

Status: `pending`

Objective:

Lock in the chat UX and local-quality improvements with targeted tests and smoke commands.

Scope:

- Add backend tests for per-request reasoning control.
- Add frontend build/type validation after chat UI changes.
- Refresh local smoke-test notes if request payloads change.
- Record any manual local Gemma 4 findings in the dated docs.

Acceptance:

- Focused backend tests pass.
- Frontend build passes.
- Manual smoke tests document current local response quality and remaining risks.

## Recommended Execution Order

1. Slice 1 first, because reasoning control and streaming clarity directly affect every quality test that follows.
2. Slice 2 next, because final answer quality is the highest-value local Gemma 4 improvement.
3. Slice 3 after Slice 1, once the baseline streaming UI is cleaner.
4. Slice 4 after text chat quality improves, because image analysis has a separate prompt and runtime behavior.
5. Slice 5 throughout the work, with final validation after each user-visible change.

## Watchpoints

- Per-request reasoning control should not break hosted Google chat.
- The UI should distinguish "reasoning generation is off" from "reasoning is hidden."
- Streaming answer text should remain stable when the final structured response arrives.
- Local Gemma 4 may still produce weak answers even after prompt improvements; document observed behavior instead of masking it.
- Avoid adding a new settings screen unless the chat-level controls become too crowded.
