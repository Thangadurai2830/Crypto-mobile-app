import 'api_config_io.dart' if (dart.library.html) 'api_config_web.dart' as impl;

/// Base URL for the Crypto Market API (backend).
/// Port 8000 must match backend run-backend.ps1 / uvicorn.
/// - Web / iOS: http://localhost:8000
/// - Android emulator: http://10.0.2.2:8000 (emulator's host machine)
class ApiConfig {
  ApiConfig._();

  static const int backendPort = 8000;
  static String get baseUrl => 'http://${impl.apiHost}:$backendPort';
  static String get wsUrl => 'ws://${impl.apiHost}:$backendPort/api/ws';

  static String get apiV1 => '$baseUrl/api/v1';
  static String get healthUrl => '$baseUrl/health';
  static String get healthDetailedUrl => '$baseUrl/health/detailed';
  static String get rootUrl => baseUrl;
  static String get metricsUrl => '$baseUrl/metrics';
}
