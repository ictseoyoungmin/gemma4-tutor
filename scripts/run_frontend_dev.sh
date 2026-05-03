#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Install Node 18+ first." >&2
  exit 1
fi

NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [[ "${NODE_MAJOR}" -lt 18 ]]; then
  echo "Node.js 18+ is required for Vite. Current version: $(node --version)" >&2
  exit 1
fi

cd web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
