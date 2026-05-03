#!/usr/bin/env bash
set -euo pipefail
export LLM_BACKEND=llama_cpp
export LLAMA_BASE_URL="${LLAMA_BASE_URL:-http://127.0.0.1:8080/v1}"
export LLAMA_API_KEY="${LLAMA_API_KEY:-local-not-required}"
uvicorn gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
