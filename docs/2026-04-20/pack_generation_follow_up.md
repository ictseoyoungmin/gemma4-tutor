# 2026-04-20 Pack Generation Follow-Up

## Summary

Today I reviewed the current repository state against `pack_generation_debug_plan.md` and organized what is actually implemented, what is partially in place, and what still remains to be fixed.

Current conclusion:

- the project now has a working worker-driven TOEIC problem generation flow,
- Ready Pack and Practice item inventory management are connected through the backend and the `문제` tab,
- validation and harness checks were added around ready-pack generation,
- but the main fallback-routing bug described in the debug plan is still not fully fixed.

Most important follow-up finding:

- `llm_invalid_fallback` and `llm_error_fallback` still return the generic seed TOEIC pack from `generate_ready_pack()`,
- and `process_job()` only swaps in a part-aware template pack when `generation_meta["strategy"] == "seed_fallback"`,
- so the repeated generic fallback-pack persistence problem can still happen in real model failure cases.

## What Is Already Implemented

### 1. Worker-based TOEIC problem generation flow

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`
- `src/gemma_tutor_edge/services.py`

Implemented pieces:

- background job type `generate_problem_set`,
- per-part requested pack counts,
- Ready Pack creation for TOEIC generation,
- Part 5 Practice item creation during worker generation,
- inventory retrieval through `problem_inventory()`.

### 2. Basic pack shaping and title deduplication

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`

Implemented pieces:

- `PACK_TEMPLATE_CATALOG` for `part2`, `part5`, and `part7`,
- `make_unique_title()` to avoid duplicate Ready Pack titles,
- template-backed fallback pack builder via `build_pack_from_template()`,
- seed fallback content via `build_seed_ready_pack()`.

### 3. Validation and harness checks around pack generation

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`
- `src/gemma_tutor_edge/harness/`

Implemented pieces:

- English-only validation for prompts, choices, and answers,
- Korean-only validation for explanations,
- harness execution through `validate_generated_pack()`,
- generation metadata with `strategy`, `validation_errors`, and `harness` at runtime.

Current limitation:

- this metadata is returned in-memory for the job result path,
- but it is not persisted with saved Ready Packs in storage.

### 4. Operator-facing problem inventory UI

Confirmed in:

- `web/src/components/workspace/ProblemTab.tsx`

Implemented pieces:

- part-by-part pack count controls,
- worker start/stop controls,
- harness run button and pass/fail preview,
- Ready Pack list and preview,
- Practice item bank list and preview,
- delete flows for Ready Packs and Practice items,
- queue/job visibility and inventory refresh behavior.

### 5. Supporting backend and regression coverage

Confirmed in:

- `tests/test_worker_queue.py`
- `tests/test_problem_inventory_management.py`

Covered today in the current codebase:

- worker can create Ready Packs,
- worker can generate mixed Ready Pack and Part 5 Practice content,
- repeated generation avoids duplicate titles,
- inventory detail and delete flow works.

## What Is Not Finished Yet

### 1. Main fallback-routing fix is still pending

Current code path:

- `generate_ready_pack()` returns `build_seed_ready_pack()` for both:
  - `llm_invalid_fallback`
  - `llm_error_fallback`
- `process_job()` only replaces the pack with `build_pack_from_template()` when:
  - `generation_meta["strategy"] == "seed_fallback"`

Impact:

- invalid or failed LLM output can still be stored as the same generic seed TOEIC pack,
- this is the exact issue described in the debug plan,
- duplicate low-quality content can still pollute Ready Pack inventory and downstream Practice generation.

### 2. Generation metadata is not persisted to storage or exposed in inventory API

Confirmed in:

- `src/gemma_tutor_edge/storage.py`
- `src/gemma_tutor_edge/schemas.py`

Current gap:

- `save_ready_pack()` stores `title`, `mode`, `difficulty`, `payload_json`, and `created_at`,
- no generation strategy, validation error list, fallback reason, or harness result is saved,
- the `ProblemInventoryResponse` and `ReadyPackDetail` schemas do not expose this metadata.

Impact:

- operators cannot distinguish true LLM output from fallback packs in the UI,
- the fallback distribution cannot yet be measured from saved inventory alone.

### 3. Practice item quality protection is not separated from fallback duplication risk

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`

Current gap:

- Part 5 Practice items are still built from the saved `pack` when possible,
- if that saved pack came from repeated generic fallback content, the Practice bank can inherit the same quality issue.

### 4. Planned regression tests for the fallback bug are still missing

Missing relative to the debug plan:

- invalid/error LLM path should still save part-aware fallback packs,
- repeated batch generation should avoid duplicated generic fallback prompts,
- requested item counts should be preserved across degraded paths,
- mixed strategy outcomes should be explicitly asserted.

## Additional Local Change Seen Today

There is also an unstaged UI cleanup in:

- `web/src/components/workspace/WorkspaceMain.tsx`

Current local diff:

- the hero title and subtitle block are commented out,
- likely to simplify the top dashboard surface visually.

## Recommended Next Work Order

1. Fix fallback routing first.
   Update `process_job()` or `generate_ready_pack()` so `llm_invalid_fallback` and `llm_error_fallback` also resolve to part-aware template packs for TOEIC problem-set generation.

2. Persist generation metadata.
   Extend Ready Pack storage and schemas so `strategy`, `validation_errors`, `error`, and `harness` survive saving and can be shown in the UI.

3. Add regression tests for the real failure mode.
   Focus first on `tests/test_worker_queue.py`.

4. Protect Part 5 Practice generation from low-value fallback content.
   Only derive Practice items from validated/generated packs or template-quality fallback packs.

5. Then improve operator visibility in the `문제` tab.
   Show fallback counts by strategy and clear generated-vs-fallback labeling.

## Suggested Definition Of Done For The Next Follow-Up

The next follow-up note should only call this work complete when:

- a 10-pack run no longer stores repeated generic seed TOEIC packs in invalid/error cases,
- every degraded TOEIC pack becomes a part-aware fallback pack,
- generation metadata is queryable from storage and visible in the UI,
- Part 5 Practice items no longer clone low-value repeated fallback content,
- new regression tests fail on the old bug and pass on the corrected flow.
