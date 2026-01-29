/// Frontend utils (mirrors backend src/utils usage in app).
/// Formatters for numbers and dates used across screens.

String formatPrice(num? value, {int decimals = 4}) {
  if (value == null) return '—';
  return value.toStringAsFixed(decimals);
}

String formatVolume(num? value, {int decimals = 0}) {
  if (value == null) return '—';
  return value.toStringAsFixed(decimals);
}

String formatPercent(double? value, {int decimals = 2}) {
  if (value == null) return '—';
  return '${value.toStringAsFixed(decimals)}%';
}

String formatDateTime(DateTime? dt) {
  if (dt == null) return '—';
  return dt.toIso8601String();
}

/// Format as currency (e.g. $15,320.45).
String formatCurrency(num? value, {int decimals = 2}) {
  if (value == null) return '—';
  return '\$${value.toStringAsFixed(decimals)}';
}
