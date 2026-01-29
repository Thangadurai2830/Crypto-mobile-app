/// Mirrors backend src/models/strategy.py SignalType.
enum SignalType {
  buy('BUY'),
  sell('SELL'),
  hold('HOLD');

  const SignalType(this.value);
  final String value;

  static SignalType? fromString(String v) {
    for (final e in SignalType.values) {
      if (e.value == v) return e;
    }
    return null;
  }
}
