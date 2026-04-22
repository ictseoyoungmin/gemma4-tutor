# Gemma Tutor Edge

Local-first English tutor agent built with **Pydantic-AI**, **FastAPI**, and a switchable LLM backend:

- **Development / fast iteration**: Gemini API
- **System test / local deployment**: `llama.cpp` OpenAI-compatible server

This scaffold is designed for the **Gemma 4 Impact Challenge** style workflow:

1. build product features quickly against a hosted API,
2. keep the agent/tool contracts stable,
3. switch the same application logic to a local inference backend for system testing and final local-first demos.

## What is included

- FastAPI backend with routes for chat, quiz generation, quiz submission, image-based analysis, and dashboard overview
- Pydantic-AI agents for:
  - tutor chat
  - quiz/content generation
  - image analysis
- provider abstraction:
  - `google` backend for Gemini API
  - `llama_cpp` backend for local `llama-server`
- SQLite persistence layer for memory, quizzes, attempts, sessions
- harness runner for contract/system checks
- docs for architecture, evaluation, and submission planning
- PowerShell and shell scripts for Windows/Linux workflows

## Quickstart

### Recommended: Docker Compose dev

Copy `.env.compose.example` to `.env` and then run:

```bash
docker compose up --build api web
```

Expected local endpoints:

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:5173`

This compose baseline currently covers:

- FastAPI backend
- Vite frontend

The local `llama.cpp` service is planned as the next compose slice.

### Runtime switching

Hosted Gemini mode:

```env
LLM_BACKEND=google
GOOGLE_MODEL=gemini-3-flash-preview
GEMINI_API_KEY=...
```

Local `llama.cpp` mode:

```env
LLM_BACKEND=llama_cpp
LLAMA_BASE_URL=http://llama:8080/v1
LLAMA_MODEL=gemma-4-e2b-it
```

The application routes stay the same in both modes.

### Gemma 4 model download helper

Model downloads are intentionally separated from the app runtime environment.

Create a dedicated download environment:

```bash
python3 -m venv .venv_hug
source .venv_hug/bin/activate
python -m pip install --upgrade pip
python -m pip install "huggingface_hub[cli]"
```

Then run:

```bash
./scripts/download_gemma4.sh
```

Windows PowerShell:

```powershell
.\scripts\download_gemma4.ps1
```

Expected model files:

- `~/models/gemma-4-E2B-it-Q4_K_M.gguf`
- `~/models/mmproj-F16.gguf`

### Legacy local fallback (`.venv`)

`docker compose` is now the recommended development path.

The older `.venv` path is still useful as a fallback when:

- Docker is unavailable
- you want to run quick local tests without containers
- you need a temporary direct-debug workflow

Fallback install:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

### Start API

```bash
./scripts/run_dev_api.sh
```

Windows PowerShell:

```powershell
.\scripts\run_dev_api.ps1
```

### Start frontend dashboard

The React/Vite dashboard lives under `web/` and requires `Node.js 18+`.

```bash
./scripts/run_frontend_dev.sh
```

Windows PowerShell:

```powershell
.\scripts\run_frontend_dev.ps1
```

### Run harness

```bash
.venv/bin/python -m gemma_tutor_edge.harness.runner --mode asgi
```

## Key environment variables

- `LLM_BACKEND`: `google` or `llama_cpp`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: for Gemini API development mode
- `GOOGLE_MODEL`: default `gemini-3-flash-preview`
- `LLAMA_BASE_URL`: OpenAI-compatible base URL, usually `http://127.0.0.1:8080/v1`
- `LLAMA_API_KEY`: placeholder for OpenAI-compatible servers, default `local-not-required`
- `LLAMA_MODEL`: logical model ID served by `llama.cpp`
- `APP_DB_PATH`: SQLite database path
- `APP_STORAGE_DIR`: storage directory for local artifacts

## Notes on backend switching

This project keeps the **same Pydantic-AI agent structure** while swapping the model/provider layer:

- Google path uses the Gemini API via API key based auth.
- `llama.cpp` path uses an OpenAI-compatible `/v1/chat/completions` endpoint.

## Current Dev Baseline

The repository currently supports:

- `docker compose` for `api` + `web`
- `.venv_hug` for model downloads
- `.venv` as a fallback path
- Gemini-backed `/v1/chat`
- Node.js 20 and npm 10 for the `web/` Vite dashboard

If the frontend fails to start, check `node --version` first. `Vite 5` requires `Node.js 18+`.

## Recommended next steps

1. Replace placeholder tutor prompts with your final education-specific system prompts.
2. Expand the retrieval layer from SQLite stubs to SQLite + Qdrant or another vector store.
3. Add AG-UI or a web frontend for richer chat UX.
4. Add nightly harness runs against your real `llama.cpp` deployment.
5. Add TTS/STT as optional modules after the core chat/quiz/memory loop is stable.


## Added in this scaffold update

### Frontend dashboard and learner workspace
A React + Vite frontend scaffold is included under `web/`.
It is designed for competition demos and currently renders:
- learner progress cards
- skill snapshot table
- background job queue
- ready quiz pack list
- achievements
- roadmap placeholders
- a separate learner workspace shell for study flow

### Background worker
A polling worker is included at `src/gemma_tutor_edge/worker.py`.
It consumes queued jobs from SQLite and now supports:
- seed-backed ready-pack generation
- validation plus fallback behavior for prebuild flows
- dashboard worker control via start/stop/status API endpoints

The dashboard can queue jobs and inspect or control the worker process without launching it manually in a separate terminal.

### Placeholder modules intentionally left for expansion
- TTS/STT pipeline
- curriculum ingestion
- long-term memory summarizer
- richer dashboard analytics
- llama.cpp system-test-only multimodal validation flow
