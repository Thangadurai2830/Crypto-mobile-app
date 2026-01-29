import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/models.dart';
import '../services/services.dart';
import '../utils/utils.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  final AnalyticsService _analytics = AnalyticsService();
  AnalyticsResponse? _data;
  int _windowHours = 24;
  String? _error;
  bool _loading = false;

  static const List<int> _windowOptions = [24, 48, 72, 168];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _analytics.getAnalytics(windowHours: _windowHours);
      setState(() {
        _data = data;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = '${e.statusCode}: ${e.message}';
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Analytics', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
        backgroundColor: AppTheme.background,
        actions: [
          DropdownButton<int>(
            value: _windowHours,
            dropdownColor: AppTheme.card,
            items: _windowOptions.map((h) => DropdownMenuItem(value: h, child: Text('${h}h', style: const TextStyle(color: AppTheme.textPrimary)))).toList(),
            onChanged: _loading
                ? null
                : (v) {
                    if (v != null) {
                      setState(() => _windowHours = v);
                      _load();
                    }
                  },
          ),
          const SizedBox(width: 8),
          IconButton(icon: const Icon(Icons.refresh, color: AppTheme.textPrimary), onPressed: _loading ? null : _load),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading && _data == null) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    }
    if (_error != null && _data == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton(onPressed: _load, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }
    if (_data == null) {
      return Center(
        child: FilledButton.icon(
          onPressed: _load,
          icon: const Icon(Icons.analytics),
          label: const Text('Load analytics'),
        ),
      );
    }
    final list = _data!.assets;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Window: ${_data!.windowHours}h', style: Theme.of(context).textTheme.titleSmall),
          Text('Computed: ${formatDateTime(_data!.computedAt)}', style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          ...list.map((a) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                color: AppTheme.card,
                child: ListTile(
                  title: Text(a.symbol),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (a.priceChangePct != null) Text('Change %: ${formatPercent(a.priceChangePct)}'),
                      if (a.rsi14 != null) Text('RSI(14): ${formatPrice(a.rsi14, decimals: 1)}'),
                      if (a.sma20 != null) Text('SMA20: ${formatPrice(a.sma20)}'),
                      if (a.macd != null)
                        Text(
                            'MACD: ${formatPrice(a.macd!.macdLine)} / ${formatPrice(a.macd!.signalLine)}'),
                      if (a.rank != null) Text('Rank: ${a.rank}'),
                    ],
                  ),
                  trailing: a.currentPrice != null ? Text(formatPrice(a.currentPrice, decimals: 2)) : null,
                ),
              )),
        ],
      ),
    );
  }
}
