$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if (-not $env:GEMINI_API_KEY -and -not $env:GOOGLE_API_KEY) {
    throw "Set GEMINI_API_KEY or GOOGLE_API_KEY first."
}
if (-not (Test-Path ".venv/Scripts/uvicorn.exe")) {
    throw "Missing .venv or uvicorn. Create the virtualenv and install dependencies first."
}
$env:LLM_BACKEND = "google"
.venv\Scripts\uvicorn.exe gemma_tutor_edge.app:app --reload --host 127.0.0.1 --port 8000
