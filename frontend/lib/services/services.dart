/// Frontend services aligned with backend src/services.
///
/// Backend → Frontend:
/// - data_ingestion  → DataIngestionService (triggerIngest, listMarkets)
/// - analytics       → AnalyticsService (getAnalytics, getPriceHistory)
/// - strategy_engine → StrategyService (runStrategy, getStrategyResults)
/// - strategy_service→ StrategyService (same)
/// - cleanup         → CleanupService (triggerCleanup)
/// - health (main.py)→ HealthService (root, health, healthDetailed)
/// - market routes   → MarketService (listMarkets, getMarket, prices, history, ws)
export 'analytics_service.dart';
export 'cleanup_service.dart';
export 'crypto_api_service.dart';
export 'data_ingestion_service.dart';
export 'health_service.dart';
export 'market_service.dart';
export 'metrics_service.dart';
export 'scheduler_service.dart';
export 'strategy_service.dart';
