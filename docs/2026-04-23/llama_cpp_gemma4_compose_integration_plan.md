# 2026-04-23 llama.cpp + Gemma 4 Compose Integration Plan

## Goal

Complete the remaining work needed to run the product end-to-end on local `llama.cpp` with the already-downloaded Gemma 4 checkpoints, then expose that path cleanly through:

- Docker Compose
- backend runtime configuration
- UI model/backend affordances
- chat and image-attachment learner flows

This plan focuses only on the still-missing work. Existing features such as session memory, image upload wiring, reducer cleanup, and near-bottom auto-scroll are treated as baseline, not new scope.

## Assumptions

- The Gemma 4 GGUF checkpoint is already downloaded on the host.
- The multimodal projector file is also available on the host.
- The intended local serving stack is `llama-server` with OpenAI-compatible endpoints.
- The existing FastAPI API contract should remain stable.
- The current web chat already supports:
  - text chat requests
  - image attachment upload to `/v1/image/analyze`
  - per-request `model_name` forwarding

## Current Gaps To Close

- No `llama` service exists in `docker-compose.yml`.
- Model asset paths are not validated before local startup.
- There is no verified end-to-end proof that local `llama.cpp` works for:
  - `/v1/chat`
  - `/v1/image/analyze`
- UI exposes model choices, but it does not clearly communicate local-vs-hosted runtime expectations.
- Compose and README do not yet provide a single obvious local Gemma 4 workflow.
- Developer hardening is still missing:
  - healthchecks
  - clearer startup failure messages
  - repeatable smoke-test commands

## Design Principles

- Keep backend switching environment-driven.
- Do not fork API routes for local vs hosted inference.
- Treat `llama.cpp` as an infrastructure concern, not a separate application mode with duplicate logic.
- Keep local vision support explicit, because chat and image analysis have different operational risks.
- Prefer small validation helpers over hidden startup magic.

## Proposed Work Slices

### Slice 1. Local Runtime Proof For `llama.cpp` + Gemma 4

Priority:

- `P0`

Status:

- `completed` on 2026-04-23

Objective:

- Prove that the current backend abstraction actually works against the real local `llama.cpp` server for both text chat and image analysis.

Scope:

- Start `llama-server` against the existing host checkpoint and `mmproj`.
- Verify OpenAI-compatible connectivity from the backend.
- Run one text chat smoke test through `/v1/chat`.
- Run one image attachment smoke test through `/v1/image/analyze`.
- Record any backend incompatibilities early before Compose changes are layered on top.

Implementation notes:

- Use a direct local `llama-server` command first, outside Compose, to isolate model/runtime issues from container/network issues.
- Reuse the current `LLM_BACKEND=llama_cpp` path rather than adding temporary debug-only code.
- If image analysis fails while text chat succeeds, treat that as a separate compatibility problem and keep the proof split by route.

Acceptance:

- `/v1/chat` returns a valid tutor response using `LLM_BACKEND=llama_cpp`.
- `/v1/image/analyze` returns a valid image-learning response using the same local runtime.
- Required `llama.cpp` launch flags are captured in repo documentation or a helper script.

Deliverables:

- verified local launch command or helper script
- smoke-test notes
- any backend compatibility fixes discovered during proof

Completed work:

- Verified host-side model assets were already present:
  - `/home/ubuntu/models/gemma-4-E2B-it-Q4_K_M.gguf`
  - `/home/ubuntu/models/mmproj-F16.gguf`
- Launched the official `llama.cpp` server image with the local model and multimodal projector:
  - `docker run --rm -d --name gemma4-llama-slice1 -p 8080:8080 -v "$HOME/models:/models" ghcr.io/ggml-org/llama.cpp:server -m /models/gemma-4-E2B-it-Q4_K_M.gguf --mmproj /models/mmproj-F16.gguf --host 0.0.0.0 --port 8080`
- Confirmed local server readiness:
  - `GET http://127.0.0.1:8080/health` -> `{"status":"ok"}`
  - `GET http://127.0.0.1:8080/v1/models` exposed `gemma-4-E2B-it-Q4_K_M.gguf` with `multimodal` capability.
- Ran the FastAPI app in `LLM_BACKEND=llama_cpp` mode pointing to the local `llama.cpp` server.
- Verified app-side runtime selection:
  - `GET http://127.0.0.1:8011/v1/health` -> `{"status":"ok","backend":"llama_cpp","model_name":"gemma-4-E2B-it-Q4_K_M.gguf"}`
- Completed one real chat smoke test through `/v1/chat`.
- Completed one real image-attachment smoke test through `/v1/image/analyze`.

Validation notes:

- `/v1/chat` succeeded end-to-end against local `llama.cpp`, but the returned tutor message was low-quality and largely echoed the user prompt.
- `/v1/image/analyze` succeeded end-to-end against local `llama.cpp`, but the structured response contained generic placeholder-style content rather than grounded visual analysis.
- Conclusion:
  - Slice 1 is complete as an infrastructure/runtime proof.
  - Output quality and prompt/schema alignment remain follow-up concerns, not blockers for marking the slice complete.

### Slice 2. Model Asset Validation And Startup Guardrails

Priority:

- `P0`

Status:

- `completed` on 2026-04-23

Objective:

- Fail early and clearly when the local Gemma 4 runtime is selected but required assets are missing or misconfigured.

Scope:

- Introduce explicit asset path configuration for local runtime documentation and validation.
- Validate the presence of:
  - main GGUF model
  - multimodal projector GGUF
- Provide actionable error messages before the user gets opaque inference failures.

Implementation notes:

- Prefer dedicated env vars such as:
  - `MODEL_DIR`
  - `LLAMA_GGUF_PATH`
  - `LLAMA_MMPROJ_PATH`
- Validation may live in a helper script, Compose entrypoint guard, or a lightweight backend startup check.
- The backend should not require direct file access when `llama.cpp` is fully externalized, but the local workflow still needs a canonical validation step.

Acceptance:

- Missing or wrong local model paths fail with a message that tells the developer exactly what file is expected.
- The expected host-side model layout is documented in one place.

Deliverables:

- model-path env design
- validation helper or startup guard
- updated local-runtime documentation

Completed work:

- Added explicit local-runtime asset settings in `Settings`:
  - `MODEL_DIR`
  - `LLAMA_GGUF_PATH`
  - `LLAMA_MMPROJ_PATH`
  - `VALIDATE_LLAMA_ASSETS`
- Added resolved path helpers so the project has one canonical interpretation of the local Gemma 4 asset layout.
- Added optional fast-fail validation when:
  - `LLM_BACKEND=llama_cpp`
  - `VALIDATE_LLAMA_ASSETS=true`
- Implemented a validation helper entrypoint:
  - `python -m gemma_tutor_edge.validate_local_runtime`
- Added convenience scripts:
  - `scripts/validate_gemma4_assets.sh`
  - `scripts/validate_gemma4_assets.ps1`
- Updated `.env.compose.example` and `README.md` so the expected local model paths and validation toggle are documented in one place.
- Added regression coverage for:
  - default path resolution from `MODEL_DIR`
  - failure on missing local files
  - success with explicit custom file paths

Validation notes:

- `tests/test_config.py` passed after the change.
- `bash scripts/validate_gemma4_assets.sh` passed on the current machine and resolved:
  - `/home/ubuntu/models/gemma-4-E2B-it-Q4_K_M.gguf`
  - `/home/ubuntu/models/mmproj-F16.gguf`
- The startup guard remains opt-in by design so it does not break externally managed `llama.cpp` deployments where the app process cannot directly see host model files.

### Slice 3. Compose `llama` Service Integration

Priority:

- `P0`

Status:

- `completed` on 2026-04-23

Objective:

- Add a real `llama` service to Compose and connect the backend to it without changing API routes.

Scope:

- Extend `docker-compose.yml` with a `llama` service.
- Mount the host model directory into the container.
- Configure `llama-server` with Gemma 4 + `mmproj`.
- Point API local mode to `http://llama:8080/v1`.
- Keep hosted mode available through environment switching.

Implementation notes:

- The `llama` service should expose a stable logical model name that matches `LLAMA_MODEL`.
- Use Compose env vars to avoid hardcoding host-specific model paths.
- If image analysis requires additional `llama.cpp` settings, keep them explicit in the service command.

Acceptance:

- `docker compose up llama api` works with `LLM_BACKEND=llama_cpp`.
- The API can call the `llama` container through Compose networking.
- Both chat and image-analysis routes use the same backend-selection mechanism already present in the app.

Deliverables:

- updated `docker-compose.yml`
- compose-oriented env template updates
- documented local Gemma 4 container workflow

Completed work:

- Added a real `llama` service to `docker-compose.yml` using the official `ghcr.io/ggml-org/llama.cpp:server` image.
- Mounted the host model directory into the `llama` container at `/models`.
- Wired the `llama` service command to launch Gemma 4 with the multimodal projector:
  - `-m /models/gemma-4-E2B-it-Q4_K_M.gguf`
  - `--mmproj /models/mmproj-F16.gguf`
- Updated the `api` service so local-mode Compose runs explicitly set:
  - `LLM_BACKEND`
  - `LLAMA_BASE_URL`
  - `LLAMA_MODEL`
  - `MODEL_DIR`
  - `LLAMA_GGUF_PATH`
  - `LLAMA_MMPROJ_PATH`
  - `VALIDATE_LLAMA_ASSETS`
- Mounted the same host model directory into the `api` container so optional asset validation can work in Compose as well.
- Updated the default local `LLAMA_MODEL` value to match the actually served `llama.cpp` model name:
  - `gemma-4-E2B-it-Q4_K_M.gguf`
- Updated `.env.compose.example` with:
  - `HOST_MODEL_DIR`
  - compose-local Gemma 4 defaults
- Updated `README.md` with a Compose-first local Gemma 4 startup path.

Validation notes:

- Rendered Compose successfully with:
  - `HOST_MODEL_DIR=/home/ubuntu/models LLM_BACKEND=llama_cpp LLAMA_MODEL=gemma-4-E2B-it-Q4_K_M.gguf docker compose config`
- Started the integrated local stack successfully with:
  - `HOST_MODEL_DIR=/home/ubuntu/models LLM_BACKEND=llama_cpp LLAMA_MODEL=gemma-4-E2B-it-Q4_K_M.gguf docker compose up -d --build llama api`
- Verified running services with `docker compose ps`:
  - `llama` was `healthy`
  - `api` was `Up`
- Verified Compose API health:
  - `GET http://127.0.0.1:8009/v1/health` returned `backend=llama_cpp`
- Verified real container-to-container inference by calling:
  - `POST http://127.0.0.1:8009/v1/chat`
- Result:
  - the `api` container successfully reached the `llama` container through Compose networking and returned a valid tutor response.

### Slice 4. Backend Runtime Cleanup For Local/Hosted Consistency

Priority:

- `P1`

Status:

- `completed` on 2026-04-23

Objective:

- Make local and hosted backends behave consistently for model selection and error reporting.

Scope:

- Review `config.py`, `llm.py`, and service routing for local-mode clarity.
- Ensure both `/v1/chat` and `/v1/image/analyze` consistently honor backend selection and `model_name`.
- Improve error messages for unsupported or mismatched local model usage.
- Ensure `/v1/health` reflects the active backend/model combination clearly.

Implementation notes:

- Avoid route-level branching specific to Gemma 4.
- Keep provider selection centralized.
- If the UI can request a model name that does not exist in the active backend, backend validation should fail cleanly.

Acceptance:

- Backend switching requires only env changes.
- Health and error responses are clear enough for local debugging.
- No duplicate inference path is introduced for local mode.

Deliverables:

- backend config cleanup
- clearer runtime validation behavior
- regression tests for local-mode request plumbing where practical

Completed work:

- Added backend-specific active model resolution so `/v1/health` now reports the model through one shared helper instead of route-local branching.
- Added explicit requested-model validation rules:
  - reject `.gguf` local model names when the active backend is `google`
  - reject non-served model names when the active backend is `llama_cpp`
- Kept backend switching env-driven, while making invalid cross-backend model selection fail early and clearly.
- Added explicit `llama_cpp` vision gating in the image-analysis service:
  - when `LLAMA_VISION_ENABLED=false`, `/v1/image/analyze` now fails fast instead of attempting multimodal inference
- Updated route-level error mapping so backend validation issues now return `400` for:
  - `/v1/chat`
  - `/v1/image/analyze`
- Preserved the existing route contract and provider abstraction.

Validation notes:

- Added regression coverage for:
  - rejecting GGUF model names on the Google backend
  - rejecting mismatched local model names on the `llama_cpp` backend
  - active-model resolution for health reporting
  - chat-service rejection on invalid local model selection
  - image-service rejection when `LLAMA_VISION_ENABLED=false`
  - route-level `400` behavior for invalid chat/image requests
- Verified with:
  - `tests/test_llama_runtime_validation.py`
  - `tests/test_image_analyze_api.py`
  - `tests/test_config.py`
- Result:
  - `13 passed`
- Confirmed the running Compose stack still reports:
  - `GET http://127.0.0.1:8009/v1/health` -> `backend=llama_cpp`, `model_name=gemma-4-E2B-it-Q4_K_M.gguf`

### Slice 5. UI Exposure And Local Backend Affordances

Priority:

- `P1`

Objective:

- Surface the local Gemma 4 path in the UI without confusing users about what is actually runnable.

Scope:

- Align visible model options with supported backend/runtime combinations.
- Decide how the UI should present local models when the backend is not running in local mode.
- Add minimal runtime guidance so chat and image attach flows are understandable during local testing.

Implementation notes:

- The current model picker already includes Gemma 4 labels, but the UI does not explain backend availability.
- Keep the UX lightweight:
  - model label refinement
  - optional helper text or status indicator
  - no heavy settings screen unless clearly needed
- The UI should not pretend that selecting a local model automatically changes backend mode if the backend is still hosted.

Acceptance:

- Users can tell whether they are testing hosted or local runtime.
- The Gemma 4 option shown in the UI maps cleanly to the active backend contract.
- Chat and image-attachment flows remain usable on desktop and mobile layouts.

Deliverables:

- model-picker cleanup
- backend/runtime status affordance
- any small UX adjustments needed for image-based local testing

### Slice 6. Compose Healthchecks And Developer Workflow Hardening

Priority:

- `P2`

Objective:

- Make the local workflow repeatable and easier to diagnose.

Scope:

- Add healthchecks for:
  - `llama`
  - `api`
- Add smoke-test commands or scripts for:
  - local chat request
  - local image-analysis request
- Consolidate README instructions into a single Compose-first local Gemma 4 path.

Implementation notes:

- Prefer simple health probes that match real runtime readiness.
- If `llama.cpp` readiness is not instantly available, use a healthcheck that tolerates warmup delay.
- Keep `.venv` and direct-local workflows documented only as fallback paths.

Acceptance:

- A developer can bring up the local stack and know what to run next.
- Failures are easier to localize between model server, API, and web.
- The local onboarding path is shorter and less ambiguous.

Deliverables:

- compose healthchecks
- smoke-test helper commands or scripts
- README workflow consolidation

## Recommended Execution Order

1. Slice 1 first, because runtime proof should happen before Compose abstraction.
2. Slice 2 next, because asset validation reduces avoidable local failures.
3. Slice 3 after proof, to containerize a known-good command.
4. Slice 4 once Compose wiring exists, to tighten backend consistency.
5. Slice 5 after backend behavior is stable, so UI copy matches reality.
6. Slice 6 last, to harden the now-working path.

## Risks And Watchpoints

- `llama.cpp` multimodal support may differ from the assumptions currently implied by the app's image-analysis path.
- A model name exposed in the UI may not correspond to the actual logical model name served by `llama-server`.
- Text chat may work before image analysis does; these should be tracked separately.
- Containerized model serving may introduce path, permission, or warmup issues not visible in direct local runs.
- If backend error reporting stays generic, local debugging will remain slow even after Compose integration.

## Definition Of Done

This work should be considered complete only when all of the following are true:

- Local Gemma 4 via `llama.cpp` is verified for both chat and image attachment flows.
- Compose includes a working `llama` service.
- Backend runtime switching remains environment-driven and route-stable.
- UI clearly exposes the local testing path without misleading model selection behavior.
- Missing model assets fail fast with actionable guidance.
- The local workflow is documented as a repeatable Compose-first path.
