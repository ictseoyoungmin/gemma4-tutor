#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:8009}"
MODEL_NAME="${MODEL_NAME:-gemma-4-E2B-it-Q4_K_M.gguf}"
USER_ID="${USER_ID:-smoke-user}"
TMP_IMAGE="$(mktemp /tmp/gemma-smoke-XXXXXX.png)"
trap 'rm -f "${TMP_IMAGE}"' EXIT

printf 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0ioAAAAASUVORK5CYII=' | base64 -d > "${TMP_IMAGE}"

echo "== API health =="
curl -fsS "${API_BASE}/v1/health"
echo
echo

echo "== Chat smoke test =="
curl -fsS -X POST "${API_BASE}/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"message\":\"Give me one short English study tip.\",\"model_name\":\"${MODEL_NAME}\"}"
echo
echo

echo "== Chat stream smoke test =="
curl -N -fsS -X POST "${API_BASE}/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"message\":\"Give me one short English study tip.\",\"model_name\":\"${MODEL_NAME}\"}"
echo
echo

echo "== Image smoke test =="
curl -fsS -X POST "${API_BASE}/v1/image/analyze" \
  -F "user_id=${USER_ID}" \
  -F "prompt=Turn this image into a short English learning activity." \
  -F "model_name=${MODEL_NAME}" \
  -F "file=@${TMP_IMAGE};type=image/png"
echo
