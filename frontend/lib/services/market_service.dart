/// Frontend service for market data (backend markets + prices + history).
/// Uses backend data from data_ingestion and market routes.
import '../models/models.dart';
import 'crypto_api_service.dart';

class MarketService {
  MarketService([CryptoApiService? api]) : _api = api ?? CryptoApiService();

  final CryptoApiService _api;

  Future<List<MarketAsset>> listMarkets() async => _api.listMarkets();
  Future<MarketAsset> getMarket(String symbol) async => _api.getMarket(symbol);
  Future<PriceRecord> getCurrentPrice(String symbol) async => _api.getCurrentPrice(symbol);
  Future<List<PriceRecord>> getHistory(String symbol, {int limit = 100}) async =>
      _api.getHistory(symbol, limit: limit);

  Stream<PriceRecord> streamPriceUpdates(String symbol) => _api.streamPriceUpdates(symbol);
}
