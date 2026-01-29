# Frontend services ↔ backend src/services

All services use [CryptoApiService](crypto_api_service.dart) (API client) and mirror backend `backend/src/services`.

| Backend (src/services) | Frontend service                                    | Methods / API                                                                                                                        |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **data_ingestion**     | [DataIngestionService](data_ingestion_service.dart) | `triggerIngest()`, `triggerIngestAndRefreshMarkets()`, `listMarkets()` → POST /markets/ingest, GET /markets                          |
| **analytics**          | [AnalyticsService](analytics_service.dart)          | `getAnalytics(windowHours)`, `getPriceHistory(symbol, limit)` → GET /analytics, GET /history; client: `computePriceChangePct`, `sma` |
| **strategy_engine**    | [StrategyService](strategy_service.dart)            | `runStrategy()`, `getStrategyResults()` → POST /strategy/run, GET /strategy/results; `strategyNames`                                 |
| **strategy_service**   | StrategyService                                     | (same as above)                                                                                                                      |
| **cleanup**            | [CleanupService](cleanup_service.dart)              | `triggerCleanup()` → POST /api/v1/cleanup                                                                                            |
| **main.py health**     | [HealthService](health_service.dart)                | `root()`, `health()`, `healthDetailed()`, `fetchAll()` → GET /, /health, /health/detailed                                            |
| **market routes**      | [MarketService](market_service.dart)                | `listMarkets()`, `getMarket()`, `getCurrentPrice()`, `getHistory()`, `streamPriceUpdates()`                                          |

Import: `import 'package:frontend/services/services.dart';` (or relative `../services/services.dart`).
