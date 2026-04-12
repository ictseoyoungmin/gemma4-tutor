# Design Gap Analysis

This document compares the implementation in this repository against the integrated design specification in [structure_and_plan/Gemma_Tutor_Edge_Integrated_Design_Spec_English.docx](./structure_and_plan/Gemma_Tutor_Edge_Integrated_Design_Spec_English.docx).

## Purpose

- Clarify what is already aligned with the target architecture.
- Identify the missing pieces required for the first reliable TOEIC MVP.
- Give the next implementation steps in delivery order rather than feature wish-list order.

## Executive Summary

The current repository already matches the intended platform architecture well:

- FastAPI is the stable API seam.
- Pydantic-AI agents are separated from deterministic services.
- The model backend can switch between hosted development and local system-test mode.
- SQLite-backed persistence, a background worker, and a harness runner are present.

The largest remaining gap is that the codebase is still a general tutor scaffold, while the design specification expects a TOEIC-first adaptive learning product with:

- a stricter TOEIC data model,
- deterministic next-question policy,
- generation validation and fallback,
- generation audit logs,
- TOEIC-specialized endpoints and tests.

## Current Alignment

### 1. Platform architecture

Aligned items:

- `FastAPI` app boundary is implemented in `src/gemma_tutor_edge/app.py`.
- Provider switching is implemented in `src/gemma_tutor_edge/llm.py`.
- Core schema contracts are implemented in `src/gemma_tutor_edge/schemas.py`.
- Background worker separation exists in `src/gemma_tutor_edge/worker.py`.
- Harness runner exists in `src/gemma_tutor_edge/harness/runner.py`.

Why this matters:

- The repository already follows the design principle of keeping the API contract stable while swapping model providers underneath.
- This is the correct base for local-first packaging and hosted-dev iteration.

### 2. Development workflow

Aligned items:

- Development with Gemini-like hosted APIs is documented in `README.md`.
- Local system-test path through `llama.cpp` is documented and reflected in config.
- The harness supports both `asgi` and `http` execution modes.

Why this matters:

- The specification explicitly assumes fast hosted iteration first and local deployment validation later.
- The current repo already supports that operating model.

### 3. Deterministic foundation

Aligned items:

- Quiz submission grading is deterministic in `src/gemma_tutor_edge/services.py`.
- SQLite persistence is already tested through unit tests.
- Worker queue flow and ready-pack persistence are already present.

Why this matters:

- The design spec emphasizes `thin-agent, thick-services`.
- The repository is already moving core reliability concerns out of the model layer.

## Partial Alignment

### 1. Quiz and TOEIC flow

Current state:

- The system can generate a quiz pack and submit answers.
- A TOEIC mode flag exists in the generic quiz pack schema.
- The flow is still pack-oriented and general-purpose rather than TOEIC-item oriented.

Gap:

- The design spec expects a first-release loop of:
  - request one TOEIC item,
  - submit one answer,
  - get immediate short explanation,
  - update weak tags and recent accuracy,
  - adapt the next item deterministically.

Impact:

- The current implementation demonstrates a tutoring scaffold, but not yet the target TOEIC MVP loop.

### 2. Dashboard and background work

Current state:

- Dashboard overview/detail routes exist.
- Ready packs and queued jobs are visible.
- Background job processing exists for placeholder prebuild flows.

Gap:

- The specification expects the background engine to support session reflection, skill updates, quiz prebuild across difficulty bands, achievement updates, and archival/log compaction.

Impact:

- The architectural slot exists, but most of the product-specific background value is still placeholder level.

### 3. Harness and evaluation

Current state:

- The harness validates route-level contract basics and latency thresholds for sample cases.

Gap:

- The specification expects additional layers:
  - tool-routing assertions,
  - behavioral quality checks,
  - retrieval grounding checks,
  - UX/tone checks,
  - TOEIC acceptance suites,
  - fallback and retry validation.

Impact:

- The repo has an eval seam, but not yet the richer eval-first discipline described in the design.

## Major Gaps

### 1. TOEIC-specialized schema model

Missing or under-modeled items:

- `part_type`
- `grammar_tag`
- `vocab_tag`
- `difficulty_level`
- `validated`
- `validation_score`
- per-attempt `selected_option`
- per-attempt `response_time_ms`
- weak-point entities
- generation logs with parse and validation status

Current limitation:

- `QuizItem` is still generic: `prompt`, `choices`, `answer`, `explanation`, `skill_tags`.

Why this is important:

- Without these fields, the app cannot implement the adaptive TOEIC loop in a deterministic and auditable way.

### 2. Adaptive policy engine

Missing capabilities:

- recent accuracy banding,
- difficulty up/down rules,
- weak-tag concentration handling,
- anti-repetition rules,
- answer-position bias protection,
- response-time-aware pacing.

Current limitation:

- There is no dedicated deterministic policy module for selecting the next TOEIC item.

Why this is important:

- The design spec is explicit that adaptation must be owned by code, not delegated to the LLM.

### 3. Generation validation and fallback pipeline

Missing capabilities:

- structured validation stages for TOEIC items,
- duplicate-option checks,
- semantic second-pass review,
- controlled retry behavior,
- alternate prompt fallback,
- validated seed/template fallback when generation fails.

Current limitation:

- Quiz generation currently trusts the agent output once the schema is accepted.

Why this is important:

- The specification treats fallback-first reliability as a core product property, especially on constrained local inference.

### 4. TOEIC-specific APIs

Missing endpoints from the design direction:

- `POST /quiz/next`
- `POST /explain`
- `GET /diagnosis/{user_id}`

Current limitation:

- The current API surface is broad and generic.

Why this is important:

- The TOEIC MVP needs a narrow, testable, item-based loop rather than only a general pack-generation API.

### 5. Auditability and observability

Missing capabilities:

- generation attempt logs,
- validation-failure reasons,
- retry traces,
- policy decision records,
- TOEIC-specific analytics views.

Why this is important:

- The design spec expects auditability for debugging, trust, and harness inspection.

## Recommended Build Order

The design specification recommends a disciplined order, and the current repository should follow it closely.

### Phase 1: Reliable TOEIC loop without heavy generation risk

Implement first:

- TOEIC item schema and attempt schema expansion
- seed-backed `POST /quiz/next`
- deterministic grading for single-item flow
- recent accuracy and weak-tag updates
- simple deterministic next-item selection

Success condition:

- One learner can request an item, answer it, receive feedback, and get an adapted next item.

### Phase 2: Controlled generation and validation

Implement next:

- LLM-generated TOEIC item path
- structural and semantic validation
- retry and fallback behavior
- generation logging

Success condition:

- Generated items are safe enough to serve without breaking the learner flow when generation fails.

### Phase 3: Diagnostics, background value, and richer harnesses

Implement next:

- diagnosis endpoint
- richer dashboard metrics
- background prebuild by difficulty range
- session reflection
- TOEIC-specific harness suites

Success condition:

- The system becomes visibly personalized and auditable, not just interactive.

## Suggested Module Targets

Recommended implementation areas:

- `src/gemma_tutor_edge/schemas.py`
  - add TOEIC item, attempt, weak-point, and generation-log schemas
- `src/gemma_tutor_edge/services.py`
  - add single-item TOEIC services and explanation flow
- `src/gemma_tutor_edge/storage.py`
  - persist weak tags, recent accuracy windows, generation logs, and TOEIC attempts
- `src/gemma_tutor_edge/app.py`
  - expose TOEIC-specific endpoints
- `src/gemma_tutor_edge/harness/`
  - add TOEIC golden cases and fallback tests
- new module such as `src/gemma_tutor_edge/policy.py`
  - own deterministic adaptation rules
- new module such as `src/gemma_tutor_edge/validation.py`
  - own generation validation and fallback rules

## Practical Conclusion

This repository is not off-track. It already implements the correct platform shell for the product vision. The main issue is not architectural mismatch, but product-depth mismatch: the codebase is still a general tutor scaffold, while the specification now clearly prioritizes a TOEIC-first adaptive tutoring MVP.

The next meaningful work should therefore avoid broad feature expansion and instead complete the narrow TOEIC loop with:

- stronger schemas,
- deterministic policy,
- validation and fallback,
- specialized endpoints,
- richer harness coverage.
