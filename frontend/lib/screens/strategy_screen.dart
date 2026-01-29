import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/models.dart';
import '../services/services.dart';

class StrategyScreen extends StatefulWidget {
  const StrategyScreen({super.key});

  @override
  State<StrategyScreen> createState() => _StrategyScreenState();
}

class _StrategyScreenState extends State<StrategyScreen> {
  final StrategyService _strategy = StrategyService();
  List<StrategyRun> _results = [];
  StrategyRun? _lastRun;
  String _strategyName = 'ma_crossover';
  int _limitPerSymbol = 100;
  String? _error;
  bool _loading = false;
  bool _running = false;

  Future<void> _loadResults() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final list = await _strategy.getStrategyResults(limit: 10);
      setState(() {
        _results = list;
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

  Future<void> _runStrategy() async {
    setState(() {
      _running = true;
      _error = null;
    });
    try {
      final run = await _strategy.runStrategy(strategyName: _strategyName, limitPerSymbol: _limitPerSymbol);
      setState(() {
        _lastRun = run;
        _results = [run, ..._results];
        _running = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = '${e.statusCode}: ${e.message}';
        _running = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _running = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    _loadResults();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Strategy', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
        backgroundColor: AppTheme.background,
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: AppTheme.textPrimary), onPressed: _loading ? null : _loadResults),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              color: AppTheme.card,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Run strategy', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      value: _strategyName,
                      decoration: const InputDecoration(labelText: 'Strategy'),
                      items: StrategyService.strategyNames.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                      onChanged: _running ? null : (v) => setState(() => _strategyName = v ?? _strategyName),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      initialValue: _limitPerSymbol.toString(),
                      decoration: const InputDecoration(labelText: 'Limit per symbol'),
                      keyboardType: TextInputType.number,
                      onChanged: _running
                          ? null
                          : (v) {
                              final n = int.tryParse(v);
                              if (n != null && n >= 10 && n <= 500) setState(() => _limitPerSymbol = n);
                            },
                    ),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                      onPressed: _running ? null : _runStrategy,
                      icon: _running ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.play_arrow),
                      label: Text(_running ? 'Running...' : 'Run'),
                    ),
                  ],
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            if (_lastRun != null) ...[
              const SizedBox(height: 16),
              Text('Last run: ${_lastRun!.strategyName} (${_lastRun!.signals.length} signals)', style: Theme.of(context).textTheme.titleSmall),
            ],
            const SizedBox(height: 24),
            Text('Recent runs', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ..._results.map((run) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  color: AppTheme.card,
                  child: ExpansionTile(
                    title: Text('${run.strategyName} — ${run.runAt.toIso8601String()}'),
                    subtitle: Text('${run.signals.length} signals'),
                    children: run.signals
                        .map((s) {
                          final signalType = SignalType.fromString(s.signal);
                          final color = signalType == SignalType.buy
                              ? AppTheme.positive
                              : signalType == SignalType.sell
                                  ? AppTheme.negative
                                  : null;
                          return ListTile(
                            dense: true,
                            title: Text(
                              '${s.symbol} ${s.signal}',
                              style: color != null ? TextStyle(color: color, fontWeight: FontWeight.w600) : null,
                            ),
                            subtitle: s.reason != null ? Text(s.reason!) : null,
                            trailing: s.priceAtSignal != null ? Text(s.priceAtSignal!) : null,
                          );
                        })
                        .toList(),
                  ),
                )),
          ],
        ),
      ),
    );
  }
}
