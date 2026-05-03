#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -x ".venv/bin/uvicorn" ]]; then
  echo "Missing .venv or uvicorn. Create the virtualenv and install dependencies first." >&2
  exit 1
fi

export LLM_BACKEND=google
.venv/bin/uvicorn gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
