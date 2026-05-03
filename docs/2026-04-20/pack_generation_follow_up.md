# 2026-04-20 Pack Generation Follow-Up

## Summary

Today I reviewed the current repository state against `pack_generation_debug_plan.md`, then continued the implementation in small slices.

Current conclusion:

- the worker-based TOEIC problem generation flow is now connected end to end,
- failed TOEIC problem-set generations no longer persist the same generic seed pack,
- Ready Pack generation metadata is now stored and shown in the `문제` tab,
- fallback pack content is now part-aware for the main TOEIC parts currently covered,
- Part 5 Practice item generation is separated from fallback-pack reuse,
- but the next bottleneck is now observability of the original failed LLM output and stronger part-specific prompting.

Most important current follow-up finding:

- `part3` is the only part currently generating healthy LLM output consistently,
- `part2`, `part5`, `part6`, and `part7` are still frequently failing validation with patterns like:
  - `answer_not_in_choices`
  - `invalid_choice_count`
  - `too_few_items`
- the UI currently shows the fallback pack and the failure type list, but it still does not show the failed original LLM attempt itself.

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

### 2. Basic pack shaping, title deduplication, and fallback routing

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`

Implemented pieces:

- `PACK_TEMPLATE_CATALOG` for `part2`, `part5`, and `part7`,
- `make_unique_title()` to avoid duplicate Ready Pack titles,
- template-backed fallback pack builder via `build_pack_from_template()`,
- seed fallback content via `build_seed_ready_pack()`.
- `generate_problem_set` now converts all non-`llm` outcomes into part-aware fallback packs before saving.

### 3. Validation and harness checks around pack generation

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`
- `src/gemma_tutor_edge/harness/`

Implemented pieces:

- English-only validation for prompts, choices, and answers,
- Korean-only validation for explanations,
- harness execution through `validate_generated_pack()`,
- generation metadata with `strategy`, `validation_errors`, and `harness` at runtime.

Additional implemented pieces:

- generation metadata is persisted with saved Ready Packs in storage,
- `ReadyQuizSummary` and `ReadyPackDetail` now expose `generation`,
- the UI can now show `strategy`, validation error count, and harness status.

### 4. Operator-facing problem inventory UI

Confirmed in:

- `web/src/components/workspace/ProblemTab.tsx`

Implemented pieces:

- part-by-part pack count controls,
- worker start/stop controls,
- harness run button and pass/fail preview,
- Ready Pack list and preview,
- Practice item bank list and preview,
- generation strategy chips and fallback counts,
- Ready Pack strategy badges and generation metadata preview,
- delete flows for Ready Packs and Practice items,
- queue/job visibility and inventory refresh behavior.

### 5. Practice item quality protection

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`

Implemented pieces:

- Part 5 Practice item generation is now strategy-aware,
- valid `llm` generation can still derive Practice items from the saved pack,
- fallback strategies now use dedicated seed Practice items instead of reusing degraded fallback pack content,
- Practice item `source` now cleanly distinguishes `worker_generated` and `seed`.

### 6. Supporting backend and regression coverage

Confirmed in:

- `tests/test_worker_queue.py`
- `tests/test_problem_inventory_management.py`

Covered today in the current codebase:

- worker can create Ready Packs,
- worker can generate mixed Ready Pack and Part 5 Practice content,
- repeated generation avoids duplicate titles,
- invalid/error fallback paths save template-backed fallback packs,
- Ready Pack generation metadata survives storage roundtrip,
- template fallback packs validate successfully,
- fallback Part 5 Practice items do not clone degraded Ready Pack content,
- inventory detail and delete flow works.

## What Is Not Finished Yet

### 1. Original failed LLM output is still not stored for UI inspection

Current code path:

- Ready Pack generation metadata stores failure type, validation list, and harness result,
- but the failed original candidate content is not yet persisted as a preview payload.

Impact:

- operators can see that a pack failed,
- but they still cannot compare the failed original LLM output against the saved fallback pack inside the UI.

### 2. Prompting is still too generic for the unstable TOEIC parts

Confirmed in:

- `src/gemma_tutor_edge/jobs.py`

Current gap:

- the TOEIC prompt is still mostly one generic instruction template with `part_type` injected,
- the validation contract is strict, but the prompt contract is not yet equally part-specific,
- `part7` still requests large item counts in one pass,
- answer normalization is not yet applied before validation.

Impact:

- `part3` may pass because its natural dialogue MCQ structure fits the current model behavior,
- `part2`, `part5`, `part6`, and `part7` remain failure-prone for structural reasons rather than only model quality.

### 3. Validation visibility in the UI is still shallow

Confirmed in:

- `web/src/components/workspace/ProblemTab.tsx`

Current gap:

- only a short subset of validation failures is shown,
- there is no grouped error summary such as `answer_not_in_choices: 20`,
- there is no dedicated failed-attempt panel separate from the saved fallback preview.

### 4. Further part coverage still needs implementation depth

Missing relative to the debug plan:

- stronger prompt contracts for `part1`, `part2`, `part4`, `part6`, and `part7`,
- item-chunk generation or retry policy for heavier parts,
- answer/choice normalization before validation,
- richer UI failure analysis tools.

## Additional Local Change Seen Today

There is also an unstaged UI cleanup in:

- `web/src/components/workspace/WorkspaceMain.tsx`

Current local diff:

- the hero title and subtitle block are commented out,
- likely to simplify the top dashboard surface visually.

## Recommended Next Work Order

1. Persist a failed LLM candidate preview.
   Save a trimmed snapshot of the invalid original output so the UI can show both the failed candidate and the fallback pack.

2. Add a dedicated failed-attempt panel in the `문제` tab.
   Show grouped validation counts, failed candidate preview, and raw failure details separately from the saved fallback pack.

3. Split the TOEIC prompt by part contract.
   Give each part its own explicit structure, especially `part2`, `part5`, `part6`, and `part7`.

4. Add answer normalization before validation.
   Normalize label-style answers like `A`, `(B)`, or `B.` back to actual choice text when possible.

5. Add retry/chunking for fragile parts.
   `part7` in particular should not try to generate large packs in one pass.

## Suggested Definition Of Done For The Next Follow-Up

The next follow-up note should only call this work complete when:

- a failed Ready Pack can show both the failed original LLM attempt and the saved fallback pack,
- the UI can summarize repeated validation failures by type,
- `part2`, `part5`, `part6`, and `part7` have stronger part-specific prompts,
- answer/choice mismatch failures are reduced by normalization,
- larger TOEIC parts no longer fail mainly because of oversized single-pass requests.
