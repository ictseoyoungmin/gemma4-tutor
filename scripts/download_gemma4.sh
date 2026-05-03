#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

VENV_DIR=".venv_hug"
BIN_DIR="${VENV_DIR}/bin"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to create ${VENV_DIR}." >&2
  exit 1
fi

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
SITE_PACKAGES="${VENV_DIR}/lib/python${PYTHON_VERSION}/site-packages"
VENV_PY="${BIN_DIR}/python"

# Rebuild the helper environment from scratch so a partial failed install does not block reruns.
rm -rf "${VENV_DIR}"
mkdir -p "${BIN_DIR}" "${SITE_PACKAGES}"

python3 -m pip install --upgrade --target "${SITE_PACKAGES}" huggingface_hub

cat > "${VENV_PY}" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${SITE_PACKAGES}\${PYTHONPATH:+:\${PYTHONPATH}}"
exec python3 "\$@"
EOF
chmod +x "${VENV_PY}"

MODEL_DIR="${MODEL_DIR:-models}"
export MODEL_DIR
mkdir -p "${MODEL_DIR}"

"${VENV_PY}" <<'PY'
import os
from huggingface_hub import hf_hub_download

repo_id = "unsloth/gemma-4-E2B-it-GGUF"
local_dir = os.environ["MODEL_DIR"]

hf_hub_download(
    repo_id=repo_id,
    filename="gemma-4-E2B-it-Q4_K_M.gguf",
    local_dir=local_dir,
)
PY

"${VENV_PY}" <<'PY'
import os
from huggingface_hub import hf_hub_download

repo_id = "unsloth/gemma-4-E2B-it-GGUF"
local_dir = os.environ["MODEL_DIR"]

hf_hub_download(
    repo_id=repo_id,
    filename="mmproj-F16.gguf",
    local_dir=local_dir,
)
PY

echo "Downloaded:"
echo "  ${MODEL_DIR}/gemma-4-E2B-it-Q4_K_M.gguf"
echo "  ${MODEL_DIR}/mmproj-F16.gguf"
