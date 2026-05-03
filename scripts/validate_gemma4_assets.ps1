$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

if (Test-Path ".venv\Scripts\python.exe") {
    $PythonBin = ".venv\Scripts\python.exe"
} else {
    $PythonBin = "python"
}

& $PythonBin -m gemma_tutor_edge.validate_local_runtime
