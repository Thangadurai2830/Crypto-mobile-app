/// Mirrors backend src/models/market.py MarketData.
/// Time-series price/volume data per asset.
class MarketData {
  const MarketData({
    required this.id,
    required this.assetId,
    required this.symbol,
    required this.price,
    this.volume,
    required this.timestamp,
    required this.createdAt,
  });

  final int id;
  final int assetId;
  final String symbol;
  final num price;
  final num? volume;
  final DateTime timestamp;
  final DateTime createdAt;

  factory MarketData.fromJson(Map<String, dynamic> json) {
    return MarketData(
      id: json['id'] as int,
      assetId: json['asset_id'] as int,
      symbol: json['symbol'] as String,
      price: num.tryParse(json['price'].toString()) ?? 0,
      volume: json['volume'] != null ? num.tryParse(json['volume'].toString()) : null,
      timestamp: DateTime.parse(json['timestamp'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'asset_id': assetId,
        'symbol': symbol,
        'price': price,
        'volume': volume,
        'timestamp': timestamp.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
      };
}
