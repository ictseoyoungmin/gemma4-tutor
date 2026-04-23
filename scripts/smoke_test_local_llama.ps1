$ErrorActionPreference = "Stop"

$ApiBase = if ($env:API_BASE) { $env:API_BASE } else { "http://127.0.0.1:8009" }
$ModelName = if ($env:MODEL_NAME) { $env:MODEL_NAME } else { "gemma-4-E2B-it-Q4_K_M.gguf" }
$UserId = if ($env:USER_ID) { $env:USER_ID } else { "smoke-user" }
$TempImage = Join-Path $env:TEMP "gemma-smoke-test.png"

[IO.File]::WriteAllBytes(
    $TempImage,
    [Convert]::FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7Z0ioAAAAASUVORK5CYII=")
)

try {
    Write-Host "== API health =="
    & curl.exe -fsS "$ApiBase/v1/health"
    Write-Host ""
    Write-Host ""

    Write-Host "== Chat smoke test =="
    & curl.exe -fsS -X POST "$ApiBase/v1/chat" `
      -H "Content-Type: application/json" `
      -d "{""user_id"":""$UserId"",""message"":""Give me one short English study tip."",""model_name"":""$ModelName""}"
    Write-Host ""
    Write-Host ""

    Write-Host "== Chat stream smoke test =="
    & curl.exe -N -fsS -X POST "$ApiBase/v1/chat/stream" `
      -H "Content-Type: application/json" `
      -d "{""user_id"":""$UserId"",""message"":""Give me one short English study tip."",""model_name"":""$ModelName""}"
    Write-Host ""
    Write-Host ""

    Write-Host "== Image smoke test =="
    & curl.exe -fsS -X POST "$ApiBase/v1/image/analyze" `
      -F "user_id=$UserId" `
      -F "prompt=Turn this image into a short English learning activity." `
      -F "model_name=$ModelName" `
      -F "file=@$TempImage;type=image/png"
    Write-Host ""
}
finally {
    Remove-Item -ErrorAction SilentlyContinue $TempImage
}
