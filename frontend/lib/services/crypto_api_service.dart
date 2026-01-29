import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/api_config.dart';
import '../models/models.dart';

/// HTTP client for the Crypto Market API (backend).
/// When backend has API_KEY_ENABLED=true, set [apiKey] to the current key.
class CryptoApiService {
  CryptoApiService({String? apiKey}) : _apiKey = apiKey;

  final String? _apiKey;
  String get _base => ApiConfig.apiV1;

  Map<String, String> get _headers {
    final m = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    if (_apiKey != null && _apiKey!.isNotEmpty) {
      m['X-API-Key'] = _apiKey!;
    }
    return m;
  }

  Future<void> _checkResponse(http.Response r) async {
    if (r.statusCode >= 200 && r.statusCode < 300) return;
    String body = r.body;
    try {
      final j = jsonDecode(body) as Map<String, dynamic>?;
      body = j?['detail']?.toString() ?? body;
    } catch (_) {}
    throw ApiException(r.statusCode, body);
  }

  /// GET / (root)
  Future<Map<String, dynamic>> root() async {
    final r = await http.get(Uri.parse(ApiConfig.rootUrl), headers: {'Accept': 'application/json'});
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// GET /health (root)
  Future<Map<String, dynamic>> health() async {
    final r = await http.get(Uri.parse(ApiConfig.healthUrl), headers: {'Accept': 'application/json'});
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// GET /api/v1/health (v1 health check)
  Future<Map<String, dynamic>> v1Health() async {
    final r = await http.get(Uri.parse('$_base/health'), headers: _headers);
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// GET /health/detailed (DB + Redis checks)
  Future<Map<String, dynamic>> healthDetailed() async {
    final r = await http.get(Uri.parse(ApiConfig.healthDetailedUrl), headers: {'Accept': 'application/json'});
    if (r.statusCode == 503) {
      final body = jsonDecode(r.body) as Map<String, dynamic>;
      return body;
    }
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// GET /metrics (Prometheus text; backend main.py)
  Future<String> getMetrics() async {
    final r = await http.get(Uri.parse(ApiConfig.metricsUrl));
    if (r.statusCode != 200) throw ApiException(r.statusCode, r.body);
    return r.body;
  }

  /// GET /api/v1/scheduler/config (backend tasks/scheduler intervals)
  Future<Map<String, dynamic>> getSchedulerConfig() async {
    final r = await http.get(Uri.parse('$_base/scheduler/config'), headers: _headers);
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// WebSocket /api/ws?symbol=... — stream of real-time price updates
  Stream<PriceRecord> streamPriceUpdates(String symbol) async* {
    final uri = Uri.parse(ApiConfig.wsUrl).replace(queryParameters: {'symbol': symbol});
    final channel = WebSocketChannel.connect(uri);
    await for (final message in channel.stream) {
      final map = jsonDecode(message as String) as Map<String, dynamic>;
      if (map.containsKey('error')) continue;
      final timestamp = map['timestamp'];
      yield PriceRecord(
        symbol: map['symbol'] as String,
        price: num.tryParse(map['price'].toString()) ?? 0,
        volume: map['volume'] != null ? num.tryParse(map['volume'].toString()) : null,
        timestamp: timestamp != null ? DateTime.tryParse(timestamp.toString()) ?? DateTime.now() : DateTime.now(),
      );
    }
  }

  /// GET /api/v1/markets
  Future<List<MarketAsset>> listMarkets() async {
    final r = await http.get(Uri.parse('$_base/markets'), headers: _headers);
    await _checkResponse(r);
    final list = jsonDecode(r.body) as List<dynamic>;
    return list.map((e) => MarketAsset.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// GET /api/v1/markets/{symbol}
  Future<MarketAsset> getMarket(String symbol) async {
    final r = await http.get(Uri.parse('$_base/markets/$symbol'), headers: _headers);
    await _checkResponse(r);
    return MarketAsset.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// POST /api/v1/markets/ingest
  Future<Map<String, dynamic>> triggerIngest() async {
    final r = await http.post(Uri.parse('$_base/markets/ingest'), headers: _headers);
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }

  /// GET /api/v1/prices/{symbol}
  Future<PriceRecord> getCurrentPrice(String symbol) async {
    final r = await http.get(Uri.parse('$_base/prices/$symbol'), headers: _headers);
    await _checkResponse(r);
    return PriceRecord.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// GET /api/v1/history/{symbol}?limit=...
  Future<List<PriceRecord>> getHistory(String symbol, {int limit = 100}) async {
    final uri = Uri.parse('$_base/history/$symbol').replace(queryParameters: {'limit': limit.toString()});
    final r = await http.get(uri, headers: _headers);
    await _checkResponse(r);
    final list = jsonDecode(r.body) as List<dynamic>;
    return list.map((e) => PriceRecord.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// GET /api/v1/analytics?window_hours=...
  Future<AnalyticsResponse> getAnalytics({int windowHours = 24}) async {
    final uri = Uri.parse('$_base/analytics').replace(queryParameters: {'window_hours': windowHours.toString()});
    final r = await http.get(uri, headers: _headers);
    await _checkResponse(r);
    return AnalyticsResponse.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// POST /api/v1/strategy/run
  Future<StrategyRun> runStrategy({
    String strategyName = 'ma_crossover',
    int limitPerSymbol = 100,
  }) async {
    final body = jsonEncode({
      'strategy_name': strategyName,
      'limit_per_symbol': limitPerSymbol,
    });
    final r = await http.post(
      Uri.parse('$_base/strategy/run'),
      headers: _headers,
      body: body,
    );
    await _checkResponse(r);
    return StrategyRun.fromJson(jsonDecode(r.body) as Map<String, dynamic>);
  }

  /// GET /api/v1/strategy/results?limit=...
  Future<List<StrategyRun>> getStrategyResults({int limit = 10}) async {
    final uri = Uri.parse('$_base/strategy/results').replace(queryParameters: {'limit': limit.toString()});
    final r = await http.get(uri, headers: _headers);
    await _checkResponse(r);
    final list = jsonDecode(r.body) as List<dynamic>;
    return list.map((e) => StrategyRun.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// POST /api/v1/cleanup — backend services/cleanup.cleanup_old_data
  Future<Map<String, dynamic>> triggerCleanup() async {
    final r = await http.post(Uri.parse('$_base/cleanup'), headers: _headers);
    await _checkResponse(r);
    return jsonDecode(r.body) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  ApiException(this.statusCode, this.message);
  final int statusCode;
  final String message;
  @override
  String toString() => 'ApiException($statusCode): $message';
}
