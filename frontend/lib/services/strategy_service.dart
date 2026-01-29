/// Frontend service mirroring backend src/services/strategy_engine and strategy_service.
/// Run strategy (POST /strategy/run) and fetch results (GET /strategy/results).
import '../models/models.dart';
import 'crypto_api_service.dart';

class StrategyService {
  StrategyService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// Backend strategy_engine.run_strategy + strategy_service.run_strategy_and_persist
  /// → POST /api/v1/strategy/run
  Future<StrategyRun> runStrategy({
    String strategyName = 'ma_crossover',
    int limitPerSymbol = 100,
  }) async {
    return _api.runStrategy(
      strategyName: strategyName,
      limitPerSymbol: limitPerSymbol,
    );
  }

  /// Fetch latest strategy runs with signals → GET /api/v1/strategy/results
  Future<List<StrategyRun>> getStrategyResults({int limit = 10}) async {
    return _api.getStrategyResults(limit: limit);
  }

  /// Allowed strategy names (mirrors backend StrategyFactory).
  static const List<String> strategyNames = ['ma_crossover', 'momentum', 'momentum_rsi'];
}
