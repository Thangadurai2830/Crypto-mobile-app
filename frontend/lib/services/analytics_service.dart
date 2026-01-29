/// Frontend service mirroring backend src/services/analytics.
/// Fetches computed analytics and price history (GET /analytics, GET /history).
import '../models/models.dart';
import 'crypto_api_service.dart';

class AnalyticsService {
  AnalyticsService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// Backend analytics.run_analytics → GET /api/v1/analytics?window_hours=...
  Future<AnalyticsResponse> getAnalytics({int windowHours = 24}) async {
    return _api.getAnalytics(windowHours: windowHours);
  }

  /// Backend analytics.get_price_history (exposed as GET /history/{symbol}) → price history.
  Future<List<PriceRecord>> getPriceHistory(String symbol, {int limit = 100}) async {
    return _api.getHistory(symbol, limit: limit);
  }

  /// Client-side: compute price change % over last [window] points (mirrors backend compute_price_change_pct).
  static double? computePriceChangePct(List<PriceRecord> history, int window) {
    if (history.length < window + 1) return null;
    final prices = history.map((e) => e.price.toDouble()).toList();
    final oldVal = prices[prices.length - 1 - window];
    final newVal = prices.last;
    if (oldVal == 0) return null;
    return (newVal - oldVal) / oldVal * 100;
  }

  /// Client-side: simple moving average of last [period] prices.
  static double? sma(List<PriceRecord> history, int period) {
    if (history.length < period) return null;
    final slice = history.reversed.take(period).map((e) => e.price.toDouble());
    return slice.reduce((a, b) => a + b) / period;
  }
}
