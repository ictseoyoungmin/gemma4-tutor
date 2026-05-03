# Harness Engineering Notes

## Principle

Treat the API contract as the stable seam.

- product iteration can change prompts
- backend can change from Gemini API to `llama.cpp`
- harness cases remain reusable as long as route contracts stay fixed

## Targets

- `asgi` mode: no external server required, good for CI
- `http` mode: hits a running instance, good for system/integration checks

## Case file shape

```yaml
case_id: chat_basic
route: chat
payload:
  user_id: demo_user
  message: "Help me study grammar"
expect_keys: [session_id, run_id, output]
max_latency_ms: 30000
```

## Next additions

- judge-based scoring
- retrieval trace assertions
- provider-specific regression dashboards
