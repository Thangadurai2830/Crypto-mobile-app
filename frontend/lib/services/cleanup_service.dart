/// Frontend service mirroring backend src/services/cleanup.
/// Triggers cleanup_old_data (POST /api/v1/cleanup).
import 'crypto_api_service.dart';

class CleanupService {
  CleanupService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// Backend cleanup.cleanup_old_data → POST /api/v1/cleanup.
  /// Returns { status, deleted: { market_data, analytics_results, strategy_runs } }.
  Future<Map<String, dynamic>> triggerCleanup() async {
    return _api.triggerCleanup();
  }
}
