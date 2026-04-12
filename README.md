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

## Recommended workflow

### 1) Development mode
Use Gemini API for faster iteration while UI, tool design, prompts, and contracts are unstable.

```powershell
$env:GEMINI_API_KEY = "..."
$env:LLM_BACKEND = "google"
uvicorn gemma_tutor_edge.app:app --reload
```

### 2) System test mode
Once flows are stable, switch to `llama.cpp` without changing the API routes or agent tool contracts.

```powershell
$env:LLM_BACKEND = "llama_cpp"
$env:LLAMA_BASE_URL = "http://127.0.0.1:8080/v1"
$env:LLAMA_MODEL = "gemma-4-e2b-it"
uvicorn gemma_tutor_edge.app:app --reload
```

## Quickstart

### Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]
```

### Environment

Copy `.env.example` to `.env` and edit values.

### Start API

```bash
uvicorn gemma_tutor_edge.app:app --reload
```

### Run harness

```bash
python -m gemma_tutor_edge.harness.runner --mode asgi
```

## Key environment variables

- `LLM_BACKEND`: `google` or `llama_cpp`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: for Gemini API development mode
- `GOOGLE_MODEL`: default `gemini-3-flash-preview`
- `LLAMA_BASE_URL`: OpenAI-compatible base URL, usually `http://127.0.0.1:8080/v1`
- `LLAMA_API_KEY`: placeholder for OpenAI-compatible servers, default `local-not-required`
- `LLAMA_MODEL`: logical model ID served by `llama.cpp`
- `APP_DB_PATH`: SQLite database path

## Notes on backend switching

This project keeps the **same Pydantic-AI agent structure** while swapping the model/provider layer:

- Google path uses the Gemini API via API key based auth.
- `llama.cpp` path uses an OpenAI-compatible `/v1/chat/completions` endpoint.

## Recommended next steps

1. Replace placeholder tutor prompts with your final education-specific system prompts.
2. Expand the retrieval layer from SQLite stubs to SQLite + Qdrant or another vector store.
3. Add AG-UI or a web frontend for richer chat UX.
4. Add nightly harness runs against your real `llama.cpp` deployment.
5. Add TTS/STT as optional modules after the core chat/quiz/memory loop is stable.


## Added in this scaffold update

### Frontend dashboard
A React + Vite dashboard scaffold is included under `web/`.
It is designed for competition demos and currently renders:
- learner progress cards
- skill snapshot table
- background job queue
- ready quiz pack list
- achievements
- roadmap placeholders

### Background worker
A polling worker is included at `src/gemma_tutor_edge/worker.py`.
It consumes queued jobs from SQLite and currently supports a deterministic placeholder path for `prebuild_quiz`.
This makes the architecture visible before the full agentic background generation is wired in.

### Placeholder modules intentionally left for expansion
- TTS/STT pipeline
- curriculum ingestion
- long-term memory summarizer
- richer dashboard analytics
- llama.cpp system-test-only multimodal validation flow
