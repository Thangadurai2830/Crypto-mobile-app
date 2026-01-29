/// Frontend service mirroring backend src/services/data_ingestion.
/// Triggers ingest (POST /markets/ingest) and refreshes market list.
import '../models/models.dart';
import 'crypto_api_service.dart';

class DataIngestionService {
  DataIngestionService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  /// Triggers backend data_ingestion.ingest_latest_prices (POST /api/v1/markets/ingest).
  /// Returns API response: { status, message }.
  Future<Map<String, dynamic>> triggerIngest() async {
    return _api.triggerIngest();
  }

  /// Trigger ingest then return refreshed market list (ensure_assets + ingest on backend).
  Future<List<MarketAsset>> triggerIngestAndRefreshMarkets() async {
    await _api.triggerIngest();
    return _api.listMarkets();
  }

  /// List markets (after ingest, data comes from backend market assets + latest price).
  Future<List<MarketAsset>> listMarkets() async {
    return _api.listMarkets();
  }
}
