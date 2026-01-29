/// Matches backend StrategySignalSchema / src/models/strategy.py StrategySignal.
class StrategySignal {
  const StrategySignal({
    this.id,
    this.runId,
    required this.symbol,
    required this.signal,
    this.priceAtSignal,
    this.reason,
    required this.createdAt,
  });

  final int? id;
  final int? runId;
  final String symbol;
  final String signal; // BUY, SELL, HOLD
  final String? priceAtSignal;
  final String? reason;
  final DateTime createdAt;

  factory StrategySignal.fromJson(Map<String, dynamic> json) {
    return StrategySignal(
      id: json['id'] as int?,
      runId: json['run_id'] as int?,
      symbol: json['symbol'] as String,
      signal: json['signal'] as String,
      priceAtSignal: json['price_at_signal'] as String?,
      reason: json['reason'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'run_id': runId,
        'symbol': symbol,
        'signal': signal,
        'price_at_signal': priceAtSignal,
        'reason': reason,
        'created_at': createdAt.toIso8601String(),
      };
}

/// Matches backend StrategyRunSchema.
class StrategyRun {
  const StrategyRun({
    required this.id,
    required this.runAt,
    required this.strategyName,
    this.paramsSnapshot,
    required this.status,
    this.signals = const [],
  });

  final int id;
  final DateTime runAt;
  final String strategyName;
  final String? paramsSnapshot;
  final String status;
  final List<StrategySignal> signals;

  factory StrategyRun.fromJson(Map<String, dynamic> json) {
    final list = json['signals'] as List<dynamic>? ?? [];
    return StrategyRun(
      id: json['id'] as int,
      runAt: DateTime.parse(json['run_at'] as String),
      strategyName: json['strategy_name'] as String,
      paramsSnapshot: json['params_snapshot'] as String?,
      status: json['status'] as String,
      signals: list.map((e) => StrategySignal.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'run_at': runAt.toIso8601String(),
        'strategy_name': strategyName,
        'params_snapshot': paramsSnapshot,
        'status': status,
        'signals': signals.map((e) => e.toJson()).toList(),
      };
}
