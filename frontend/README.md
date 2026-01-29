# Crypto Market — Flutter Frontend

Flutter app for the Crypto Market API. Connects to the backend at **http://localhost:8000** (see [CONNECTING.md](../CONNECTING.md) in repo root).

## Backend ↔ Frontend

| Backend                               | Frontend                                     |
| ------------------------------------- | -------------------------------------------- |
| `backend/run-backend.ps1` (port 8000) | `frontend/run-frontend.ps1`                  |
| `backend/requirements.txt`            | `pubspec.yaml` + `flutter pub get`           |
| `backend/alembic.ini` (migrations)    | N/A (frontend uses API only)                 |
| `backend/pytest.ini` (tests)          | `test/` + `flutter test`                     |
| `backend/.dockerignore`               | `frontend/.gitignore` (build/cache excluded) |

## Run

1. Start the backend: from repo root run `.\backend\run-backend.ps1`.
2. From repo root: `.\frontend\run-frontend.ps1`  
   Or from this folder: `flutter pub get` then `flutter run`.
3. Pick Chrome (web), or an iOS/Android emulator. API base URL is in `lib/core/api_config.dart` (localhost:8000; Android emulator uses 10.0.2.2:8000).

## Tests

- Widget tests: `flutter test test/widget_test.dart`
- API contract tests (backend must be running): `flutter test test/integration/api_contract_test.dart`

## Structure

- `lib/core/api_config.dart` — backend base URL and endpoints.
- `lib/services/` — API client and services (markets, analytics, strategy, health, scheduler, metrics, cleanup).
- `lib/models/` — DTOs aligned with backend API.
- `lib/screens/` — Markets, Analytics, Strategy, API Status (health, scheduler config, metrics, cleanup).
