/// Mirrors backend src/models/market.py CryptoAsset.
/// Master table for crypto assets (one row per symbol).
class CryptoAsset {
  const CryptoAsset({
    required this.id,
    required this.symbol,
    this.name,
    this.coingeckoId,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final String symbol;
  final String? name;
  final String? coingeckoId;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory CryptoAsset.fromJson(Map<String, dynamic> json) {
    return CryptoAsset(
      id: json['id'] as int,
      symbol: json['symbol'] as String,
      name: json['name'] as String?,
      coingeckoId: json['coingecko_id'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'symbol': symbol,
        'name': name,
        'coingecko_id': coingeckoId,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };
}
