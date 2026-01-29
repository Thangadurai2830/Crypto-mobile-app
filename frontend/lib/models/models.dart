/// Frontend models aligned with backend src/models and API schemas.
///
/// Backend mapping:
/// - backend/src/models/market.py  → CryptoAsset, MarketData; API view → MarketAsset, PriceRecord
/// - backend/src/models/analytics.py → AnalyticsResult; API → AnalyticsResponse, AssetAnalytics, MacdData
/// - backend/src/models/strategy.py → StrategyRun, StrategySignal, SignalType
/// - backend/src/models/user.py     → User, UserProfile, AccountStatus, KycLevel, LoginHistory, Session

export 'analytics.dart';
export 'analytics_result.dart';
export 'crypto_asset.dart';
export 'login_history.dart';
export 'market_asset.dart';
export 'market_data.dart';
export 'price_record.dart';
export 'session.dart';
export 'signal_type.dart';
export 'strategy.dart';
export 'user.dart';
