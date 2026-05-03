# 2026-04-22 Docker Compose + llama.cpp + Gemma 4 Migration Plan

## Goal

Move the project from a primarily `.venv`-driven local development workflow to a `docker compose`-driven workflow, while introducing:

- flexible backend switching between the current hosted API path and local `llama.cpp`
- local Gemma 4 serving via `llama.cpp`
- a dedicated `.venv_hug` environment for Hugging Face model download tasks
- a clear model asset layout for GGUF and multimodal projector files

The end state should preserve the current FastAPI contract and allow the application to switch between hosted and local inference without changing the API routes.

## Current State

Observed from the codebase:

- the backend already supports `LLM_BACKEND=google | llama_cpp | test`
- provider switching is implemented in [src/gemma_tutor_edge/llm.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/llm.py:1)
- runtime settings are centralized in [src/gemma_tutor_edge/config.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/config.py:1)
- the project is still documented and scripted around `.venv`
- there is no checked-in `docker-compose.yml`
- there is no dedicated workflow yet for downloading or mounting local GGUF assets

## Migration Principles

- keep the current FastAPI application contract stable
- make provider switching environment-driven, not code-path-fragmented
- separate runtime concerns from one-time model download concerns
- keep local Gemma 4 optional, not mandatory, for every developer
- make the Docker path the default dev path, while still allowing escape hatches for direct local runs when needed

## Target Architecture

### Services

Planned `docker compose` services:

- `api`: FastAPI backend
- `web`: Vite frontend or built frontend container, depending on dev/prod mode
- `llama`: local `llama-server` exposing OpenAI-compatible API
- optional `worker`: background job worker if we want it isolated from `api`

### Persistent volumes / bind mounts

- `./data` -> app data and sqlite persistence
- `~/models` or a configurable host model directory -> GGUF and `mmproj` assets
- source bind mounts for dev mode

### Runtime switching

The application should support:

- hosted mode:
  - `LLM_BACKEND=google`
  - `GOOGLE_API_KEY` or `GEMINI_API_KEY`
  - `GOOGLE_MODEL=<hosted model>`
- local mode:
  - `LLM_BACKEND=llama_cpp`
  - `LLAMA_BASE_URL=http://llama:8080/v1` inside compose
  - `LLAMA_MODEL=<logical served model name>`

The UI should continue passing `model_name`, but backend routing should remain backend-aware:

- hosted path uses Google provider
- local path uses OpenAI-compatible `llama.cpp` server

## Gemma 4 Model Assets

Required assets for the requested local multimodal Gemma 4 setup:

- main GGUF model
- multimodal projector GGUF

Requested download commands:

```bash
huggingface-cli download unsloth/gemma-4-E2B-it-GGUF \
  gemma-4-E2B-it-Q4_K_M.gguf \
  --local-dir ~/models \
  --local-dir-use-symlinks False

huggingface-cli download unsloth/gemma-4-E2B-it-GGUF \
  mmproj-F16.gguf \
  --local-dir ~/models \
  --local-dir-use-symlinks False
```

Recommended host layout:

```text
~/models/
  gemma-4-E2B-it-Q4_K_M.gguf
  mmproj-F16.gguf
```

## Dedicated `.venv_hug` Plan

Purpose:

- isolate Hugging Face download tooling from the main backend runtime environment
- avoid polluting the app runtime virtualenv with download-only dependencies

Recommended scope for `.venv_hug`:

- `huggingface_hub[cli]`
- optional authentication helpers if private/gated assets are added later

Suggested commands:

```bash
python3 -m venv .venv_hug
source .venv_hug/bin/activate
python -m pip install --upgrade pip
python -m pip install "huggingface_hub[cli]"
```

Optional helper script to add:

- `scripts/download_gemma4.sh`
- `scripts/download_gemma4.ps1`

That script should:

- activate `.venv_hug` or fail clearly if missing
- ensure target model directory exists
- run both `huggingface-cli download` commands
- print the expected final file paths

## Compose Plan

### Slice 1. Compose baseline for API + web

Scope:

- add `docker-compose.yml`
- add `Dockerfile.api`
- add `Dockerfile.web` if needed for frontend dev/prod split
- mount `./data`
- provide `.env.compose` or documented compose env strategy

Acceptance:

- `docker compose up api web` works for standard development
- backend still responds on `/v1/health`
- frontend can reach the backend through compose networking or configured host port mapping

Status:

- `completed`

Completed work:

- Added [docker-compose.yml](/home/ubuntu/gemma_tutor_edge/docker-compose.yml:1) with `api` and `web` services.
- Added [Dockerfile.api](/home/ubuntu/gemma_tutor_edge/Dockerfile.api:1) for the FastAPI backend.
- Added [Dockerfile.web](/home/ubuntu/gemma_tutor_edge/Dockerfile.web:1) for the Vite frontend.
- Added [.dockerignore](/home/ubuntu/gemma_tutor_edge/.dockerignore:1) to keep Docker build context smaller and cleaner.
- Added [.env.compose.example](/home/ubuntu/gemma_tutor_edge/.env.compose.example:1) as a compose-oriented environment template.
- Updated [README.md](/home/ubuntu/gemma_tutor_edge/README.md:53) so compose is now documented as the recommended development entry point.

Validation note:

- The current workspace does not have a `docker` CLI available, so `docker compose up` and `docker compose config` could not be executed from this session.
- The files were created against the current repository layout and existing Python/Node entrypoints, but runtime validation still needs to be performed on a machine with Docker installed.

### Slice 2. Local `llama.cpp` service integration

Scope:

- add `llama` service to compose
- mount model directory into container
- configure `llama-server` launch flags for Gemma 4 + `mmproj`
- point backend local mode to `http://llama:8080/v1`

Acceptance:

- `docker compose up llama api` allows `LLM_BACKEND=llama_cpp`
- backend chat and image analysis paths can hit local server through the existing provider abstraction

### Slice 3. Environment and model-switch policy cleanup

Scope:

- tighten config naming and defaults around `google_model`, `llama_model`, and local URLs
- document clear switching scenarios:
  - hosted-only
  - local-only
  - hybrid dev workflow
- ensure image-analysis path and standard tutor-chat path both respect backend selection consistently

Acceptance:

- changing only env vars is enough to switch runtime backend
- no route-level code changes are required to move between hosted and local inference

### Slice 4. `.venv_hug` download workflow

Scope:

- add setup instructions for `.venv_hug`
- add download helper scripts
- document required Hugging Face auth assumptions
- validate model asset presence before starting local `llama.cpp`

Acceptance:

- a new developer can download the required Gemma 4 assets without touching the main runtime environment
- missing model files fail with a clear, actionable error

### Slice 5. Developer experience hardening

Scope:

- add healthchecks for `api` and `llama`
- add `make` targets or scripts for common workflows
- update README to make compose the primary path
- keep `.venv` path documented only as fallback or advanced mode

Acceptance:

- the default onboarding path is obvious
- backend mode switching is documented in one place

## Recommended Config Changes

Planned config evolution in [src/gemma_tutor_edge/config.py](/home/ubuntu/gemma_tutor_edge/src/gemma_tutor_edge/config.py:1):

- keep `LLM_BACKEND` as the top-level selector
- keep `GOOGLE_MODEL`
- keep `LLAMA_MODEL`
- keep `LLAMA_BASE_URL`
- add explicit model-path-oriented env vars for local documentation or startup validation if needed:
  - `MODEL_DIR`
  - `LLAMA_GGUF_PATH`
  - `LLAMA_MMPROJ_PATH`

Note:

- the backend itself may not need file paths if `llama-server` is fully externalized into its own service
- file-path env vars are still useful for validation scripts and compose templates

## Recommended `llama-server` Launch Shape

Expected local multimodal launch shape:

```bash
llama-server \
  -m /models/gemma-4-E2B-it-Q4_K_M.gguf \
  --mmproj /models/mmproj-F16.gguf \
  --host 0.0.0.0 \
  --port 8080
```

Potential follow-up tuning later:

- context size
- GPU layer offload
- batch size
- chat template handling
- explicit alias / served model naming

## API Compatibility Considerations

The key requirement is flexible switching between existing API-backed mode and local Gemma 4 mode.

This means:

- keep FastAPI routes unchanged
- keep `sendChatMessage` and image-analysis entrypoints unchanged from the frontend point of view
- treat provider choice as backend runtime configuration
- avoid embedding local-model assumptions into frontend code

## Risks

- multimodal support in `llama.cpp` may have model-specific quirks and should be smoke-tested separately from text-only chat
- local Gemma 4 latency may be meaningfully higher than hosted mode, especially on CPU-only setups
- model naming between UI labels and actual served `llama.cpp` identifiers can drift unless normalized
- Docker networking and host-mounted model directories can become brittle across machines if not documented carefully

## Recommended Execution Order

1. Add compose baseline for `api` and `web`
2. Add `llama` service and local backend env wiring
3. Add `.venv_hug` download workflow and helper scripts
4. Update README and dev scripts so compose becomes the default path
5. Run smoke tests for:
   - hosted text chat
   - local text chat
   - local image analysis

## Concrete Deliverables

Files likely to be added or changed:

- `docker-compose.yml`
- `Dockerfile.api`
- optionally `Dockerfile.web`
- `.dockerignore`
- `scripts/download_gemma4.sh`
- `scripts/download_gemma4.ps1`
- `README.md`
- `src/gemma_tutor_edge/config.py`
- possibly `src/gemma_tutor_edge/llm.py`
- optional startup validation helper for local model mode

## Definition of Done

- Docker Compose is the documented default development path
- local `llama.cpp` Gemma 4 service can be started through compose
- `.venv_hug` is documented and usable for model downloads
- backend can switch between hosted API mode and local Gemma 4 mode via env vars
- existing FastAPI and frontend contracts remain stable
