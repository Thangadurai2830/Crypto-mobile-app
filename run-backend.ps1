# Run the Crypto App backend (CORS enabled for Flutter web). Must run from THIS folder (Crypto App).
# Usage: from "Crypto App" folder run: .\run-backend.ps1
$BackendDir = Join-Path $PSScriptRoot "backend"
Set-Location $BackendDir
$env:PYTHONPATH = $BackendDir
Write-Host "Starting Crypto App backend at http://localhost:8000 (CORS allows Flutter web)" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Cyan
& python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
