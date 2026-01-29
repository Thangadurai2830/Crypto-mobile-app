/// Frontend service mirroring backend health endpoints.
/// Root, health, health/detailed (DB + Redis checks).
import 'crypto_api_service.dart';

class HealthService {
  HealthService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// GET / (root)
  Future<Map<String, dynamic>> root() async {
    return _api.root();
  }

  /// GET /health
  Future<Map<String, dynamic>> health() async {
    return _api.health();
  }

  /// GET /api/v1/health
  Future<Map<String, dynamic>> v1Health() async {
    return _api.v1Health();
  }

  /// GET /health/detailed (DB + Redis checks; may return 503)
  Future<Map<String, dynamic>> healthDetailed() async {
    return _api.healthDetailed();
  }

  /// Fetch all health info (root + health + detailed) for API Status screen.
  Future<HealthStatus> fetchAll() async {
    final rootData = await _api.root();
    final healthData = await _api.health();
    final detailedData = await _api.healthDetailed();
    return HealthStatus(
      root: rootData,
      health: healthData,
      healthDetailed: detailedData,
    );
  }
}

class HealthStatus {
  const HealthStatus({
    required this.root,
    required this.health,
    required this.healthDetailed,
  });
  final Map<String, dynamic> root;
  final Map<String, dynamic> health;
  final Map<String, dynamic> healthDetailed;
}
