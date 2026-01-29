/// Matches backend MarketAssetWithLatestPrice (MarketAssetSchema + latest price/volume).
class MarketAsset {
  const MarketAsset({
    required this.id,
    required this.symbol,
    this.name,
    this.coingeckoId,
    required this.createdAt,
    required this.updatedAt,
    this.latestPrice,
    this.latestVolume,
    this.latestTimestamp,
  });

  final int id;
  final String symbol;
  final String? name;
  final String? coingeckoId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final num? latestPrice;
  final num? latestVolume;
  final DateTime? latestTimestamp;

  factory MarketAsset.fromJson(Map<String, dynamic> json) {
    return MarketAsset(
      id: json['id'] as int,
      symbol: json['symbol'] as String,
      name: json['name'] as String?,
      coingeckoId: json['coingecko_id'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      latestPrice: json['latest_price'] != null ? num.tryParse(json['latest_price'].toString()) : null,
      latestVolume: json['latest_volume'] != null ? num.tryParse(json['latest_volume'].toString()) : null,
      latestTimestamp: json['latest_timestamp'] != null ? DateTime.tryParse(json['latest_timestamp'] as String) : null,
    );
  }

  /// API response shape (MarketAssetWithLatestPrice); use for sending if needed.
  Map<String, dynamic> toJson() => {
        'id': id,
        'symbol': symbol,
        'name': name,
        'coingecko_id': coingeckoId,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
        'latest_price': latestPrice,
        'latest_volume': latestVolume,
        'latest_timestamp': latestTimestamp?.toIso8601String(),
      };
}
