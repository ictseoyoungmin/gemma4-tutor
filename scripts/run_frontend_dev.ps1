 $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
 $ProjectRoot = Split-Path -Parent $ScriptDir
 Set-Location $ProjectRoot

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is not installed. Install Node 18+ first."
}
$nodeVersion = [int](node -p "process.versions.node.split('.')[0]")
if ($nodeVersion -lt 18) {
    throw "Node.js 18+ is required for Vite. Current version: $(node --version)"
}
Set-Location web
npm install
npm run dev -- --host 127.0.0.1 --port 5173
