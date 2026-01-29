# Frontend tests

- **widget_test.dart** — Widget tests for CryptoApp (no backend required).
- **integration/api_contract_test.dart** — API contract tests mirroring backend `tests/integration/test_api.py`. Require backend running at `ApiConfig.baseUrl` (e.g. `cd backend && python -m uvicorn src.main:app --port 8000`). Run: `flutter test test/integration/api_contract_test.dart`.
