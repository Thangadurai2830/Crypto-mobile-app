# Connecting Backend and Flutter Frontend

## Backend (FastAPI)

| Backend file / concept  | Purpose                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------- |
| **run-backend.ps1**     | Run API: `.\backend\run-backend.ps1` → uvicorn on port **8000**                     |
| **requirements.txt**    | Points to `requirements/base.txt`; install: `pip install -r requirements.txt`       |
| **alembic.ini**         | DB migrations; run: `cd backend && alembic upgrade head`                            |
| **crypto_analytics.db** | SQLite DB (created by app/migrations); backend uses it, frontend talks via API only |
| **pytest.ini**          | Backend tests: `cd backend && pytest`                                               |
| **.dockerignore**       | Docker build excludes venv, **pycache**, \*.db, .env, etc.                          |

- **API base:** `http://localhost:8000` (same as run-backend.ps1 port)
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **API v1:** `/api/v1` (markets, prices, history, analytics, strategy, cleanup, scheduler)

## CORS (Flutter web)

Flutter web runs on a **random port** (e.g. `http://localhost:60996`). The backend allows any `http://localhost:*` and `http://127.0.0.1:*` origin when `cors_allow_localhost_any_port=True` (default in `backend/src/core/config.py`), using both `allow_origin_regex` in CORSMiddleware and a custom LocalhostCORSMiddleware for preflight. **Restart the backend** after changing CORS or if you see "blocked by CORS policy" in the browser console. Ensure the backend you run is from **this repo** (Crypto App) so CORS is configured correctly.

## Flutter Frontend

| Frontend equivalent          | Purpose                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------- |
| **run-frontend.ps1**         | Run app: `.\frontend\run-frontend.ps1` → `flutter pub get` then `flutter run` |
| **pubspec.yaml**             | Dependencies (like requirements.txt); run: `flutter pub get`                  |
| **lib/core/api_config.dart** | Base URL for backend (localhost:8000 / Android 10.0.2.2:8000)                 |
| **test/**                    | Widget + integration tests (mirrors backend pytest)                           |
| **.gitignore**               | Excludes build/, .dart_tool/, etc. (similar idea to backend .dockerignore)    |

- **Run:** From repo root: `.\frontend\run-frontend.ps1` or from `frontend`: `flutter run`
- **API base:** Configured in `lib/core/api_config.dart`:
  - **Web / iOS:** `http://localhost:8000`
  - **Android emulator:** `http://10.0.2.2:8000` (emulator’s host)

## Connection checklist (backend ↔ frontend)

| Backend (FastAPI)                                                            | Frontend (Flutter)                                           |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `GET /`, `/health`, `/api/v1/health`                                         | `HealthService`, Health screen                               |
| `GET /api/v1/markets`, `GET /api/v1/markets/{symbol}`                        | `MarketService`, Markets tab, Market detail screen           |
| `GET /api/v1/prices/current/{symbol}`, `GET /api/v1/prices/history/{symbol}` | `MarketService.getCurrentPrice`, `getHistory`, Market detail |
| WebSocket `/api/v1/prices/stream/{symbol}`                                   | `MarketService.streamPriceUpdates`                           |
| `GET /api/v1/analytics`                                                      | `AnalyticsService`, Analytics screen                         |
| `POST /api/v1/strategy/run`, `GET /api/v1/strategy/results`                  | `StrategyService`, Strategy screen                           |
| `POST /api/v1/ingest`, `POST /api/v1/cleanup`                                | `DataIngestionService`, `CleanupService`, Health/Markets UI  |
| `GET /api/v1/scheduler/config`                                               | Health screen (scheduler config)                             |
| `GET /metrics` (Prometheus)                                                  | Health screen link to metrics URL                            |

API docs: **http://localhost:8000/docs** (also linked from Health screen).

## Quick start

1. **Backend (must be from this Crypto App folder for CORS):** From **Crypto App** root run `.\run-backend.ps1` or `.\backend\run-backend.ps1`. Do **not** run the backend from a different project (e.g. "Crypto market website") or CORS will block the Flutter web app.
2. **Migrations (first time):** `cd backend && alembic upgrade head`
3. **Frontend:** `.\frontend\run-frontend.ps1` (or `cd frontend && flutter pub get && flutter run`)
4. Open app; choose Chrome for web or a device/emulator. Frontend will call backend at port 8000.

## Docker (backend)

- Build/run from `backend/docker` (see `backend/docker/DEPLOY.md`). `.dockerignore` excludes venv, cache, db, .env.
- When backend runs in Docker, point frontend at the host/port where the API is exposed (e.g. `localhost:8000` or your machine’s IP for a physical device).
