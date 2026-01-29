# Run the backend API (dev: SQLite, no Docker required).
# From repo root or backend folder:
#   .\backend\run-backend.ps1
# or from backend folder:
#   .\run-backend.ps1

$BackendDir = $PSScriptRoot
if (-not $BackendDir) { $BackendDir = ".\backend" }
Set-Location $BackendDir

$env:PYTHONPATH = $BackendDir
Write-Host "Starting backend at http://localhost:8000 (API docs: http://localhost:8000/docs)" -ForegroundColor Green
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
