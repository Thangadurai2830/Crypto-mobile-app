/// Frontend service for backend main.py /metrics (Prometheus).
import 'crypto_api_service.dart';

class MetricsService {
  MetricsService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// GET /metrics — Prometheus text (request count, latency).
  Future<String> getMetrics() async {
    return _api.getMetrics();
  }
}
