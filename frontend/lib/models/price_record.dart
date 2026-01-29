/// Matches backend PriceRecordSchema (symbol, price, volume, timestamp).
class PriceRecord {
  const PriceRecord({
    required this.symbol,
    required this.price,
    this.volume,
    required this.timestamp,
  });

  final String symbol;
  final num price;
  final num? volume;
  final DateTime timestamp;

  factory PriceRecord.fromJson(Map<String, dynamic> json) {
    return PriceRecord(
      symbol: json['symbol'] as String,
      price: num.tryParse(json['price'].toString()) ?? 0,
      volume: json['volume'] != null ? num.tryParse(json['volume'].toString()) : null,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'symbol': symbol,
        'price': price,
        'volume': volume,
        'timestamp': timestamp.toIso8601String(),
      };
}
