#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if [[ ! -x ".venv_hug/bin/hf" ]]; then
  echo "Missing .venv_hug or hf CLI. Create .venv_hug and install huggingface_hub first." >&2
  exit 1
fi

MODEL_DIR="${MODEL_DIR:-$HOME/models}"
mkdir -p "${MODEL_DIR}"

.venv_hug/bin/hf download unsloth/gemma-4-E2B-it-GGUF \
  gemma-4-E2B-it-Q4_K_M.gguf \
  --local-dir "${MODEL_DIR}"

.venv_hug/bin/hf download unsloth/gemma-4-E2B-it-GGUF \
  mmproj-F16.gguf \
  --local-dir "${MODEL_DIR}"

echo "Downloaded:"
echo "  ${MODEL_DIR}/gemma-4-E2B-it-Q4_K_M.gguf"
echo "  ${MODEL_DIR}/mmproj-F16.gguf"
