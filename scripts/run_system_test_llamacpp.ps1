$ErrorActionPreference = "Stop"
$env:LLM_BACKEND = "llama_cpp"
if (-not $env:LLAMA_BASE_URL) { $env:LLAMA_BASE_URL = "http://127.0.0.1:8080/v1" }
if (-not $env:LLAMA_API_KEY) { $env:LLAMA_API_KEY = "local-not-required" }
uvicorn gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
