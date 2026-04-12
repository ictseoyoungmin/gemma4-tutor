#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=src
python -m gemma_tutor_edge.worker "$@"
