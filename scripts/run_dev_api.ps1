$ErrorActionPreference = "Stop"
if (-not $env:GEMINI_API_KEY -and -not $env:GOOGLE_API_KEY) {
    throw "Set GEMINI_API_KEY or GOOGLE_API_KEY first."
}
$env:LLM_BACKEND = "google"
uvicorn gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
