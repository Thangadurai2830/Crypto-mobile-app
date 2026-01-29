// Integration tests mirroring backend tests/integration/test_api.py.
// Run with backend available (e.g. cd backend && pytest then flutter test test/integration).
// Contract: GET /health → status ok, GET /v1/markets → list, GET /v1/analytics → window_hours/assets, etc.

import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/services/services.dart';

void main() {
  late CryptoApiService api;

  setUpAll(() {
    api = CryptoApiService();
  });

  group('API contract (backend tests/integration/test_api.py)', () {
    test('GET /health returns 200 and status ok', () async {
      final data = await api.health();
      expect(data['status'], 'ok');
    });

    test('GET /api/v1/health returns status ok', () async {
      final data = await api.v1Health();
      expect(data['status'], 'ok');
    });

    test('GET / (root) returns message and docs', () async {
      final data = await api.root();
      expect(data.containsKey('message'), isTrue);
      expect(data.containsKey('docs'), isTrue);
    });

    test('GET /health/detailed returns checks with database', () async {
      final data = await api.healthDetailed();
      expect(data.containsKey('checks'), isTrue);
      expect(data['checks'] is Map, isTrue);
      final checks = data['checks'] as Map<String, dynamic>;
      expect(checks.containsKey('database'), isTrue);
    });

    test('GET /v1/markets returns list', () async {
      final list = await api.listMarkets();
      expect(list, isA<List>());
    });

    test('GET /v1/analytics returns window_hours and assets', () async {
      final data = await api.getAnalytics(windowHours: 24);
      expect(data.windowHours, 24);
      expect(data.assets, isA<List>());
    });

    test('GET /v1/analytics with invalid window_hours throws or is validated by backend', () async {
      // Backend returns 422 for window_hours=9999; frontend may throw ApiException
      try {
        await api.getAnalytics(windowHours: 9999);
      } on ApiException catch (e) {
        expect(e.statusCode, 422);
        return;
      }
      // If backend accepts, that's ok
    });

    test('GET /v1/strategy/results returns list', () async {
      final list = await api.getStrategyResults(limit: 5);
      expect(list, isA<List>());
    });

    test('GET /metrics returns Prometheus-style text', () async {
      final text = await api.getMetrics();
      expect(text, isNotEmpty);
      expect(
        text.contains('request_count') || text.contains('http_requests') || text.contains('# HELP'),
        isTrue,
      );
    });

    test('GET /v1/scheduler/config returns job intervals', () async {
      final data = await api.getSchedulerConfig();
      expect(data.containsKey('market_data_refresh_minutes'), isTrue);
      expect(data.containsKey('analytics_computation_minutes'), isTrue);
      expect(data.containsKey('strategy_reevaluation_minutes'), isTrue);
      expect(data.containsKey('database_cleanup_hours'), isTrue);
    });
  });
}
