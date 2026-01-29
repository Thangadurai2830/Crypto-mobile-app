/// Mirrors backend src/models/analytics.py AnalyticsResult.
/// Computed analytics per symbol and time window.
class AnalyticsResult {
  const AnalyticsResult({
    required this.id,
    required this.symbol,
    required this.windowHours,
    this.priceChangePct,
    this.volumeChangePct,
    this.momentum,
    this.currentPrice,
    this.currentVolume,
    required this.computedAt,
  });

  final int id;
  final String symbol;
  final int windowHours;
  final double? priceChangePct;
  final double? volumeChangePct;
  final double? momentum;
  final num? currentPrice;
  final num? currentVolume;
  final DateTime computedAt;

  factory AnalyticsResult.fromJson(Map<String, dynamic> json) {
    return AnalyticsResult(
      id: json['id'] as int,
      symbol: json['symbol'] as String,
      windowHours: json['window_hours'] as int,
      priceChangePct: (json['price_change_pct'] as num?)?.toDouble(),
      volumeChangePct: (json['volume_change_pct'] as num?)?.toDouble(),
      momentum: (json['momentum'] as num?)?.toDouble(),
      currentPrice: json['current_price'] != null ? num.tryParse(json['current_price'].toString()) : null,
      currentVolume: json['current_volume'] != null ? num.tryParse(json['current_volume'].toString()) : null,
      computedAt: DateTime.parse(json['computed_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'symbol': symbol,
        'window_hours': windowHours,
        'price_change_pct': priceChangePct,
        'volume_change_pct': volumeChangePct,
        'momentum': momentum,
        'current_price': currentPrice,
        'current_volume': currentVolume,
        'computed_at': computedAt.toIso8601String(),
      };
}
