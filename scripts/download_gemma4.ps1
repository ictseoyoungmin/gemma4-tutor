$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if (-not (Test-Path ".venv_hug/Scripts/hf.exe")) {
    throw "Missing .venv_hug or hf CLI. Create .venv_hug and install huggingface_hub first."
}

$ModelDir = if ($env:MODEL_DIR) { $env:MODEL_DIR } else { Join-Path $HOME "models" }
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

& .venv_hug\Scripts\hf.exe download unsloth/gemma-4-E2B-it-GGUF `
  gemma-4-E2B-it-Q4_K_M.gguf `
  --local-dir $ModelDir

& .venv_hug\Scripts\hf.exe download unsloth/gemma-4-E2B-it-GGUF `
  mmproj-F16.gguf `
  --local-dir $ModelDir

Write-Host "Downloaded:"
Write-Host "  $ModelDir/gemma-4-E2B-it-Q4_K_M.gguf"
Write-Host "  $ModelDir/mmproj-F16.gguf"
