#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://llama:8080/v1/chat/completions}"

curl -sN -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-4-E2B-it-Q4_K_M.gguf",
    "messages": [
      {"role": "user", "content": "Give me one short English study tip."}
    ],
    "temperature": 0.2,
    "max_tokens": 128,
    "stream": true
  }' | python3 - <<'PY'
import sys, json

for line in sys.stdin:
    line = line.strip()
    if not line.startswith("data: "):
        continue
    payload = line[6:]
    if payload == "[DONE]":
        break
    try:
        obj = json.loads(payload)
        delta = obj["choices"][0].get("delta", {})
        text = delta.get("content", "")
        if text:
            print(text, end="", flush=True)
    except Exception:
        pass
print()
PY