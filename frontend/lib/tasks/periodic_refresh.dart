/// Client-side periodic refresh (mirrors backend src/tasks/scheduler concept).
/// Use to auto-refresh markets/analytics at an interval without backend scheduler.
import 'dart:async';

typedef PeriodicCallback = Future<void> Function();

/// Runs [callback] every [interval] (e.g. Duration(minutes: 5)).
/// Returns a [Timer]; call [Timer.cancel] to stop.
Timer startPeriodicRefresh(Duration interval, PeriodicCallback callback) {
  return Timer.periodic(interval, (_) => callback());
}
