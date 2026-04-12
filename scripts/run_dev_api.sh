#!/usr/bin/env bash
set -euo pipefail
export LLM_BACKEND=google
uvicorn gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
