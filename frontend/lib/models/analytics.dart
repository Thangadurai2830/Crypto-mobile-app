/// Matches backend MacdSchema.
class MacdData {
  const MacdData({
    required this.macdLine,
    required this.signalLine,
    required this.histogram,
  });

  final double macdLine;
  final double signalLine;
  final double histogram;

  factory MacdData.fromJson(Map<String, dynamic> json) {
    return MacdData(
      macdLine: (json['macd_line'] as num).toDouble(),
      signalLine: (json['signal_line'] as num).toDouble(),
      histogram: (json['histogram'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'macd_line': macdLine,
        'signal_line': signalLine,
        'histogram': histogram,
      };
}

/// Matches backend AssetAnalyticsSchema.
class AssetAnalytics {
  const AssetAnalytics({
    required this.symbol,
    this.priceChangePct,
    this.volumeChangePct,
    this.momentum,
    this.currentPrice,
    this.currentVolume,
    this.windowHours = 24,
    this.sma20,
    this.ema20,
    this.volumeRatio20,
    this.rsi14,
    this.macd,
    this.rank,
  });

  final String symbol;
  final double? priceChangePct;
  final double? volumeChangePct;
  final double? momentum;
  final num? currentPrice;
  final num? currentVolume;
  final int windowHours;
  final double? sma20;
  final double? ema20;
  final double? volumeRatio20;
  final double? rsi14;
  final MacdData? macd;
  final int? rank;

  factory AssetAnalytics.fromJson(Map<String, dynamic> json) {
    return AssetAnalytics(
      symbol: json['symbol'] as String,
      priceChangePct: (json['price_change_pct'] as num?)?.toDouble(),
      volumeChangePct: (json['volume_change_pct'] as num?)?.toDouble(),
      momentum: (json['momentum'] as num?)?.toDouble(),
      currentPrice: json['current_price'] != null ? num.tryParse(json['current_price'].toString()) : null,
      currentVolume: json['current_volume'] != null ? num.tryParse(json['current_volume'].toString()) : null,
      windowHours: json['window_hours'] as int? ?? 24,
      sma20: (json['sma_20'] as num?)?.toDouble(),
      ema20: (json['ema_20'] as num?)?.toDouble(),
      volumeRatio20: (json['volume_ratio_20'] as num?)?.toDouble(),
      rsi14: (json['rsi_14'] as num?)?.toDouble(),
      macd: json['macd'] != null ? MacdData.fromJson(json['macd'] as Map<String, dynamic>) : null,
      rank: json['rank'] as int?,
    );
  }

  Map<String, dynamic> toJson() => {
        'symbol': symbol,
        'price_change_pct': priceChangePct,
        'volume_change_pct': volumeChangePct,
        'momentum': momentum,
        'current_price': currentPrice,
        'current_volume': currentVolume,
        'window_hours': windowHours,
        'sma_20': sma20,
        'ema_20': ema20,
        'volume_ratio_20': volumeRatio20,
        'rsi_14': rsi14,
        'macd': macd?.toJson(),
        'rank': rank,
      };
}

/// Matches backend AnalyticsResponse.
class AnalyticsResponse {
  const AnalyticsResponse({
    required this.windowHours,
    required this.computedAt,
    required this.assets,
  });

  final int windowHours;
  final DateTime computedAt;
  final List<AssetAnalytics> assets;

  factory AnalyticsResponse.fromJson(Map<String, dynamic> json) {
    final list = json['assets'] as List<dynamic>? ?? [];
    return AnalyticsResponse(
      windowHours: json['window_hours'] as int? ?? 24,
      computedAt: DateTime.parse(json['computed_at'] as String),
      assets: list.map((e) => AssetAnalytics.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'window_hours': windowHours,
        'computed_at': computedAt.toIso8601String(),
        'assets': assets.map((e) => e.toJson()).toList(),
      };
}
