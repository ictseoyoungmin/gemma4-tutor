# 2026-04-13 Work Log And Next Steps

## Summary

Today focused on three areas:

- understanding the current scaffold against the integrated design spec,
- verifying the real local development environment end to end,
- evolving the frontend from a dashboard-only scaffold into a dashboard plus learner workspace.

## Completed Today

### 1. Design and project understanding

Reviewed:

- `README.md`
- `docs/architecture.md`
- `docs/harness.md`
- `docs/evaluation.md`
- `docs/worker_design.md`
- `docs/frontend_dashboard.md`
- `docs/structure_and_plan/Gemma_Tutor_Edge_Integrated_Design_Spec_English.docx`

Outcome:

- Confirmed the project is structured around a stable FastAPI and Pydantic-AI contract layer.
- Confirmed the intended workflow is hosted Gemini for rapid iteration and local `llama.cpp` for system tests.
- Confirmed the design spec expects a TOEIC-first adaptive MVP, while the current repository is still a broader tutor scaffold.

Related document:

- `design_gap_analysis.md`

### 2. Gap analysis document

Created the design-gap summary based on the integrated design specification.

Current canonical path:

- `docs/2026-04-13/design_gap_analysis.md`

What it covers:

- architecture already aligned with the design,
- partial alignment areas,
- missing TOEIC-specialized schema and policy pieces,
- recommended implementation order.

### 3. Python environment and tests

Completed:

- created `.venv`,
- installed backend dependencies,
- ran backend tests,
- confirmed async SQLite tests pass when executed outside the restricted sandbox.

Verified test result:

- full pytest suite passed: `5 passed`

### 4. Real API verification

Verified:

- `.env` Gemini key path,
- FastAPI app startup,
- `/v1/health` success,
- real `/v1/chat` success through the app layer using Gemini.

Notes:

- initial failure was caused by an invalid API key in `.env`,
- after replacing it with a valid key, chat responses succeeded.

### 5. Frontend runtime verification

Completed:

- checked frontend dev prerequisites,
- installed Node.js and npm,
- discovered Ubuntu package Node 12 was too old for Vite 5,
- upgraded to Node 20 via NodeSource,
- installed `web` dependencies,
- verified Vite dev server starts and responds locally,
- verified production build succeeds.

Verified local frontend runtime:

- `node v20.20.2`
- `npm 10.8.2`
- `npm run build` passed
- Vite dev server responded on `http://127.0.0.1:5173`

### 6. Dev script improvements

Updated scripts so they work when executed from the `scripts/` directory instead of assuming the repo root as the current working directory.

Updated:

- `scripts/run_dev_api.sh`
- `scripts/run_dev_api.ps1`
- `scripts/run_frontend_dev.sh`
- `scripts/run_frontend_dev.ps1`

Additional improvements:

- backend scripts now require `.venv`,
- frontend scripts validate `Node.js 18+`,
- frontend script starts Vite on `127.0.0.1:5173`.

### 7. README refresh

Updated `README.md` to reflect the current verified local development setup:

- backend should be run through the helper script,
- frontend requires Node 18+,
- the current environment was validated with Gemini and Vite.

### 8. Frontend product structure change

Changed the frontend from dashboard-only to a two-surface model:

- Dashboard
- Learner Workspace

Updated files:

- `web/src/App.tsx`
- `web/src/components/LearnerWorkspace.tsx`
- `docs/frontend_dashboard.md`
- `README.md`

Result:

- dashboard remains intact for analytics and background-job visibility,
- learner workspace now exists as a dedicated study surface shell.

### 9. Real tutor chat wiring in learner workspace

Implemented a real chat panel connected to `/v1/chat`.

Added or updated:

- `web/src/components/TutorChatPanel.tsx`
- `web/src/api.ts`
- `web/src/types.ts`
- `web/src/components/LearnerWorkspace.tsx`
- removed `web/src/components/ChatWorkspacePlaceholder.tsx`

Implemented behavior:

- sends real tutor messages,
- stores and reuses `session_id`,
- renders conversation history,
- shows suggested next actions from tutor responses,
- surfaces request errors in the panel.

### 10. CORS fix for frontend chat

Problem encountered:

- browser preflight `OPTIONS /v1/chat` failed with `405 Method Not Allowed`,
- learner workspace chat showed `Failed to fetch`.

Fix applied:

- added FastAPI `CORSMiddleware` for local Vite origins,
- added a regression test for chat preflight.

Updated:

- `src/gemma_tutor_edge/app.py`
- `tests/test_cors.py`

Verified:

- backend test pass including the new CORS test.

### 11. Learner Workspace UI fidelity pass

Updated the learner workspace so it now tracks `.reference/learner_workspace_v2.html` much more closely instead of only borrowing the overall visual tone.

Completed:

- aligned the top navigation, left tutor chat column, center learning sections, and right study-status rail with the reference layout,
- replaced the oversized inline-style workspace implementation with smaller workspace-focused components,
- moved shared learner-workspace styling into a dedicated CSS file with shared tokens and responsive breakpoints,
- preserved the real `/v1/chat` integration while restyling the tutor panel to match the reference more faithfully.

Added or reorganized:

- `web/src/components/workspace/workspace.css`
- `web/src/components/workspace/workspaceData.ts`
- `web/src/components/workspace/WorkspaceNav.tsx`
- `web/src/components/workspace/WorkspaceMain.tsx`
- `web/src/components/workspace/WorkspaceRightRail.tsx`
- `web/src/components/workspace/TutorChatPanel.tsx`
- thin wrappers in `web/src/components/LearnerWorkspace.tsx` and `web/src/components/TutorChatPanel.tsx`

Verified:

- frontend production build still succeeds after the refactor.

### 12. TOEIC single-item follow-up

Implemented the next follow-up slice from the recommended order:

- added a seed-backed TOEIC Part 5 single-item flow,
- added `POST /v1/quiz/next` for deterministic item selection,
- added `POST /v1/quiz/answer` for immediate grading and explanation,
- stored TOEIC attempt history including selected option and response time,
- added a learner-workspace practice panel wired to the real backend flow,
- changed tutor suggested-action chips to send immediately instead of only filling the draft field.

Added or updated:

- `src/gemma_tutor_edge/schemas.py`
- `src/gemma_tutor_edge/services.py`
- `src/gemma_tutor_edge/storage.py`
- `src/gemma_tutor_edge/app.py`
- `src/gemma_tutor_edge/toeic.py`
- `tests/test_toeic_flow.py`
- `web/src/api.ts`
- `web/src/types.ts`
- `web/src/components/workspace/PracticePanel.tsx`
- `web/src/components/workspace/WorkspaceMain.tsx`
- `web/src/components/workspace/TutorChatPanel.tsx`
- `web/src/components/workspace/workspace.css`

Verified:

- backend tests pass: `8 passed`
- frontend production build succeeds with the new practice panel

### 13. Ready Pack launcher follow-up

Implemented the next recommended learner-workspace follow-up:

- added a launch path from stored ready packs into a live quiz session,
- reused the existing quiz submission route for launched ready packs,
- replaced the workspace's static ready-pack list with live backend data,
- added an in-workspace ready-pack solving panel with immediate score and feedback.

Added or updated:

- `src/gemma_tutor_edge/schemas.py`
- `src/gemma_tutor_edge/services.py`
- `src/gemma_tutor_edge/storage.py`
- `src/gemma_tutor_edge/app.py`
- `tests/test_worker_queue.py`
- `web/src/api.ts`
- `web/src/types.ts`
- `web/src/components/workspace/ReadyPackPanel.tsx`
- `web/src/components/workspace/WorkspaceMain.tsx`
- `web/src/components/workspace/workspace.css`

Verified:

- backend tests still pass: `8 passed`
- frontend production build still succeeds

### 14. Ready Pack generation quality follow-up

Improved the background prebuild path so it no longer creates obvious placeholder packs.

Implemented:

- a seed-backed ready-pack generator for TOEIC and grammar modes,
- deterministic validation for quiz-pack structure,
- worker-side LLM attempt plus validation plus fallback behavior,
- generation metadata in worker results so the prebuild path is more auditable.

Added or updated:

- `src/gemma_tutor_edge/jobs.py`
- `tests/test_worker_queue.py`

Verified:

- backend tests still pass: `8 passed`
- frontend production build still succeeds

## Current State

The project can now be described like this:

- Backend app runs locally from `.venv`.
- Gemini-backed tutor chat works through the FastAPI app.
- Frontend runs with Vite on Node 20.
- The frontend is no longer dashboard-only.
- Learner Workspace exists and can call the real tutor chat route.
- Learner Workspace now visually follows the v2 reference structure much more closely and is split into smaller maintainable files.
- Learner Workspace now includes a real TOEIC Part 5 single-item practice panel with immediate answer feedback.

## Remaining Work

### High priority product work

- Add persistence and UI for ready-pack generation metadata and audit traces.
- Expand the prebuild path from seed-backed packs to richer TOEIC-specialized pack generation.

### Backend domain work

- Add TOEIC-specialized schema fields such as `part_type`, `grammar_tag`, `difficulty_level`, and validation status.
- Implement deterministic adaptive policy logic for next-question selection.
- Add generation validation, retry, and fallback behavior.
- Add generation logs and auditability for question creation.

### Frontend learner workspace work

- Auto-send suggested next actions when clicked instead of only copying them into the draft field.
- Add a real practice panel for TOEIC item presentation and answer submission.
- Add ready-pack entry points from learner workspace.
- Add image lesson and audio panels beyond placeholders.

### Dashboard work

- Keep dashboard as a separate progress and operations surface.
- Add stronger analytics around recent accuracy, weak tags, streaks, and difficulty progression.
- Add clearer links from dashboard state to learner actions.

### Testing and evaluation work

- Expand harness coverage beyond contract checks into TOEIC acceptance scenarios.
- Add frontend smoke checks if UI automation is introduced later.
- Add regression tests for new learner workspace API flows.
- Add nightly checks for local-model provider switching and multimodal paths.

### Documentation work

- Keep `docs/frontend_dashboard.md` aligned with the actual frontend structure.
- Add a dedicated learner-workspace document once practice flow and quiz interaction are real.
- Update README again when TOEIC learner flow becomes first-class.

## Recommended Next Order

1. Implement a real TOEIC practice panel in Learner Workspace.
2. Add backend service and storage support for single-item adaptive study flow.
3. Connect ready-pack launch and answer submission end to end.
4. Expand dashboard metrics after the learner flow is stable.

## Files Most Relevant After Today

- `src/gemma_tutor_edge/app.py`
- `src/gemma_tutor_edge/services.py`
- `src/gemma_tutor_edge/schemas.py`
- `tests/test_cors.py`
- `web/src/App.tsx`
- `web/src/api.ts`
- `web/src/types.ts`
- `web/src/components/LearnerWorkspace.tsx`
- `web/src/components/TutorChatPanel.tsx`
- `web/src/components/workspace/workspace.css`
- `web/src/components/workspace/workspaceData.ts`
- `web/src/components/workspace/WorkspaceNav.tsx`
- `web/src/components/workspace/WorkspaceMain.tsx`
- `web/src/components/workspace/WorkspaceRightRail.tsx`
- `web/src/components/workspace/TutorChatPanel.tsx`
- `docs/2026-04-13/design_gap_analysis.md`
- `docs/frontend_dashboard.md`
- `README.md`
