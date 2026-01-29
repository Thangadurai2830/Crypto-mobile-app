# Run the Flutter frontend (connects to backend at http://localhost:8000).
# From repo root:
#   .\frontend\run-frontend.ps1
# From frontend folder:
#   .\run-frontend.ps1
# Ensure backend is running first: .\backend\run-backend.ps1

$FrontendDir = $PSScriptRoot
if (-not $FrontendDir) { $FrontendDir = ".\frontend" }
Set-Location $FrontendDir

Write-Host "Frontend connects to backend at http://localhost:8000 (see CONNECTING.md)" -ForegroundColor Cyan
Write-Host "Run backend first: .\backend\run-backend.ps1" -ForegroundColor Yellow
Write-Host "Installing dependencies..." -ForegroundColor Green
flutter pub get
Write-Host "Starting Flutter app (choose Chrome for web, or device/emulator)..." -ForegroundColor Green
flutter run
