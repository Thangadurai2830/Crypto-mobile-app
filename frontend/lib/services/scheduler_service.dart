/// Frontend service mirroring backend src/tasks/scheduler.
/// Fetches scheduler config (job intervals) from GET /api/v1/scheduler/config.
import 'crypto_api_service.dart';

class SchedulerService {
  SchedulerService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// Backend tasks/scheduler.py job intervals (from config).
  Future<Map<String, dynamic>> getSchedulerConfig() async {
    return _api.getSchedulerConfig();
  }
}
