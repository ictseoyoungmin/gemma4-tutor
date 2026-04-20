# 2026-04-20 Pack Generation Debug Plan

## Summary

Today should focus on stabilizing TOEIC problem-pack generation quality.

Current product issue:

- when generating 10 packs, only around 1 to 2 are created as intended,
- too many packs fall back to duplicated seed-like content,
- the fallback path is obscuring the real generation failure rate and degrading the learner-facing inventory.

This plan follows the same working style used in `docs/2026-04-13/work_log_and_next_steps.md` and the target product direction described in `docs/structure_and_plan/Gemma_Tutor_Edge_Integrated_Design_Spec_English.docx`.

## Problem Statement

Observed product symptom:

- Ready Pack generation appears successful from the worker/UI point of view,
- but a large share of generated packs are silently replaced with repeated fallback content,
- this makes the inventory noisy and reduces trust in both the worker and the generated curriculum.

Most immediate code-level suspicion:

- `src/gemma_tutor_edge/jobs.py` returns a generic seed pack from `generate_ready_pack()` whenever LLM generation is invalid or errors,
- `process_job()` only swaps in `build_pack_from_template()` when `generation_meta["strategy"] == "seed_fallback"`,
- therefore `llm_invalid_fallback` and `llm_error_fallback` can still persist the same repeated seed pack instead of a part-aware fallback pack.

This likely explains why duplicate low-quality packs accumulate even when titles are unique.

## Working Hypothesis

Primary hypothesis:

- the current fallback policy is inconsistent across `seed_fallback`, `llm_invalid_fallback`, and `llm_error_fallback`,
- invalid or failed LLM output is being converted to the same generic seed TOEIC pack too early,
- the worker stores that fallback result as if it were a generated pack.

Secondary hypotheses to verify:

- validation rules may be too strict relative to the agent output format, causing excessive fallback,
- prompt quality may be underspecifying part-specific structure for `part2`, `part6`, and `part7`,
- harness validation may pass/fail differently from `validate_quiz_pack()`, making diagnosis harder,
- the UI does not yet surface fallback reason distribution clearly enough to spot the real failure mode quickly.

## Goals For Today

1. Reproduce the issue deterministically and measure how many packs land in each generation strategy bucket.
2. Identify the exact branch where repeated seed content is being introduced.
3. Refactor fallback behavior so every failed TOEIC pack generation uses a part-aware fallback instead of the same generic seed pack.
4. Preserve Korean pack titles and Korean explanations while keeping questions and answer choices in English.
5. Add regression coverage so a 10-pack generation batch cannot silently degrade into mostly duplicated seed content again.

## Step-By-Step Plan

### 1. Reproduce and inspect generation outcomes

Do first:

- run a real generation batch with multiple pack counts, especially `part5`, `part6`, and mixed-part requests,
- collect the per-pack `strategy`, validation error list, and harness result,
- inspect saved `ready_packs` payloads for repeated prompt/choice patterns,
- confirm whether the bad packs come from `seed_fallback`, `llm_invalid_fallback`, or `llm_error_fallback`.

Expected output:

- a small table or log snapshot showing how many packs fall into each strategy bucket,
- at least one concrete failing example for each major fallback path.

### 2. Add temporary debug visibility before changing behavior

Add or verify:

- generation metadata persistence for each saved pack,
- clear worker logs for `strategy`, `error`, `validation_errors`, and harness failures,
- optional UI exposure in the `문제` tab so fallback-heavy runs are visible without opening raw DB rows.

Reason:

- if fallback remains silent, the team cannot distinguish model-quality issues from fallback-policy bugs.

### 3. Fix fallback routing in the worker

Refactor target:

- unify fallback handling so `llm_invalid_fallback` and `llm_error_fallback` do not store the generic `build_seed_ready_pack()` output for TOEIC problem-set generation,
- ensure all failed TOEIC pack generations are converted into a part-specific fallback pack with the requested `item_count`, `difficulty`, and `part_type`,
- keep `prebuild_quiz` behavior separated if needed, because its current generic fallback is less harmful than the multi-pack inventory case.

Likely implementation direction:

- move part-aware fallback selection closer to `generate_problem_set`,
- or return a richer fallback type from `generate_ready_pack()` so callers can decide how to degrade safely,
- or replace `build_seed_ready_pack()` for TOEIC mode with a template-backed fallback that is not globally identical.

### 4. Improve generation quality before fallback

After fallback routing is corrected:

- review the agent prompt for each TOEIC part,
- add a bounded retry path for validation failures before degrading,
- keep retries cheap and observable rather than silently masking them.

Success condition for this step:

- the system should distinguish between:
  - valid first-pass generation,
  - retry-success generation,
  - controlled template fallback,
  - hard error fallback.

### 5. Separate Practice item generation from duplicated pack content

Current risk:

- `part5` practice items are derived from the saved pack content,
- if the pack was a duplicated fallback, the practice bank quality also degrades.

Planned adjustment:

- only derive practice items from validated/generated or template-quality packs,
- avoid feeding obviously duplicated low-value fallback items into the practice bank,
- preserve seed practice fallback separately as an explicit emergency path.

### 6. Add regression tests

Required test coverage:

- mixed strategy batch where invalid/error generation still stores part-aware fallback packs rather than the same generic seed pack,
- repeated generation batch does not save duplicated fallback prompts across many packs,
- saved pack item counts match requested template counts,
- questions/choices remain English and explanations remain Korean,
- `part5` practice-item generation does not duplicate the same fallback content across the bank.

Suggested focus files:

- `tests/test_worker_queue.py`
- possibly a new targeted test around `generate_ready_pack()` or worker generation metadata.

### 7. Tighten UI feedback for operators

Add or improve in the `문제` tab:

- fallback counts by strategy,
- failed validation reason summaries,
- easier distinction between true generated packs and template fallback packs,
- optional cleanup workflow for deleting bad packs after verification.

Reason:

- the operator should be able to tell whether a batch is healthy without opening each pack manually.

## Proposed Execution Order

1. reproduce batch behavior and gather concrete examples,
2. add logging/metadata visibility if needed,
3. fix fallback routing for `llm_invalid_fallback` and `llm_error_fallback`,
4. add regression tests,
5. improve prompt/retry behavior,
6. expose fallback quality signals in UI,
7. clean up already-polluted data and verify with a fresh run.

## Definition Of Done

This work should be considered complete when:

- a 10-pack generation batch no longer produces mostly duplicated seed-based packs,
- fallback packs, when needed, are part-aware and visibly marked,
- worker metadata clearly explains why each pack was generated, retried, or degraded,
- `part5` practice items are not mostly cloned from the same bad fallback source,
- regression tests fail on the old buggy behavior and pass on the new behavior,
- a fresh UI run shows a cleaner inventory without hidden duplication.

## Notes And Risks

- the immediate priority is fallback correctness, not prompt perfection,
- a better prompt alone will not fix the current storage bug if the wrong fallback object is still persisted,
- existing dirty DB rows should not be used as proof of success after the fix; verification should use a fresh database or a cleaned inventory,
- if hosted-model variance remains high after the fallback fix, the next task should be structured retry policy plus stronger per-part generation templates.

## Expected Deliverables

- worker fallback-path fix in `src/gemma_tutor_edge/jobs.py`,
- stronger regression tests in `tests/`,
- improved operator visibility in the `문제` tab,
- a short follow-up work log documenting actual root cause, applied fix, and post-fix generation rate.
