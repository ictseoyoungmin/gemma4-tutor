# Architecture

## Core idea

The product uses a single application stack while switching only the model provider:

- **dev path**: Gemini API for rapid iteration
- **system-test path**: `llama.cpp` OpenAI-compatible local server

## Layers

1. **API layer**: FastAPI routes and request validation
2. **Agent layer**: Pydantic-AI tutor, quiz, and vision agents
3. **Deterministic service layer**: quiz grading, session bookkeeping, dashboard aggregation
4. **Persistence layer**: SQLite for memory, quizzes, attempts
5. **Harness layer**: contract and latency checks against ASGI app or running HTTP server

## Why this split matters

The provider swap stays below the agent/service layer. That keeps:

- prompts stable,
- tool signatures stable,
- API contracts stable,
- harness cases reusable.

## Extension points

- replace SQLite retrieval with SQLite + Qdrant
- add AG-UI frontend
- add STT/TTS workers
- add background scheduler for prebuilding quiz packs
- add durable orchestration for long jobs
