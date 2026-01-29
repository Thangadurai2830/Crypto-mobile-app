import 'package:flutter/material.dart';

import '../core/api_config.dart';
import '../core/app_theme.dart';
import '../services/services.dart';

/// API docs URL (backend main.py docs_url="/docs").
String get apiDocsUrl => '${ApiConfig.baseUrl}/docs';

class HealthScreen extends StatefulWidget {
  const HealthScreen({super.key});

  @override
  State<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends State<HealthScreen> {
  final HealthService _health = HealthService();
  final CleanupService _cleanup = CleanupService();
  final SchedulerService _scheduler = SchedulerService();
  final MetricsService _metrics = MetricsService();
  Map<String, dynamic>? _root;
  Map<String, dynamic>? _healthData;
  Map<String, dynamic>? _healthDetailed;
  Map<String, dynamic>? _schedulerConfig;
  String? _error;
  bool _loading = false;
  bool _cleanupRunning = false;

  Future<void> _loadAll() async {
    setState(() {
      _loading = true;
      _error = null;
      _root = null;
      _healthData = null;
      _healthDetailed = null;
      _schedulerConfig = null;
    });
    try {
      final status = await _health.fetchAll();
      Map<String, dynamic>? sched;
      try {
        sched = await _scheduler.getSchedulerConfig();
      } catch (_) {}
      setState(() {
        _root = status.root;
        _healthData = status.health;
        _healthDetailed = status.healthDetailed;
        _schedulerConfig = sched;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _error = '${e.statusCode}: ${e.message}';
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Backend unreachable at ${ApiConfig.baseUrl}. Start it with: backend\\run-backend.ps1';
        _loading = false;
      });
    }
  }

  Future<void> _showMetrics() async {
    try {
      final text = await _metrics.getMetrics();
      if (!mounted) return;
      showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Prometheus metrics'),
          content: SingleChildScrollView(
            child: SelectableText(text, style: Theme.of(context).textTheme.bodySmall),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Close')),
          ],
        ),
      );
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Metrics: ${e.message}')));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Cannot reach backend at ${ApiConfig.baseUrl}. Start it with: backend\\run-backend.ps1'),
          ),
        );
      }
    }
  }

  Future<void> _runCleanup() async {
    setState(() => _cleanupRunning = true);
    try {
      final result = await _cleanup.triggerCleanup();
      if (mounted) {
        final deleted = result['deleted'] as Map<String, dynamic>?;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Cleanup: ${deleted ?? result}')),
        );
      }
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Cleanup: ${e.message}')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Cleanup: $e')));
    }
    if (mounted) setState(() => _cleanupRunning = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('API Status', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
        backgroundColor: AppTheme.background,
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: AppTheme.textPrimary), onPressed: _loading ? null : _loadAll),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Base URL: ${ApiConfig.baseUrl}', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            SelectableText('API docs: $apiDocsUrl', style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loading ? null : _loadAll,
              icon: _loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.health_and_safety),
              label: Text(_loading ? 'Loading...' : 'Check health'),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _cleanupRunning ? null : _runCleanup,
              icon: _cleanupRunning ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.cleaning_services),
              label: Text(_cleanupRunning ? 'Cleanup...' : 'Trigger cleanup (backend)'),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _showMetrics,
              icon: const Icon(Icons.bar_chart),
              label: const Text('View metrics (GET /metrics)'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Card(
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_error!),
                ),
              ),
            ],
            if (_root != null) ...[
              const SizedBox(height: 16),
              _section('GET / (root)', _root!),
            ],
            if (_healthData != null) ...[
              const SizedBox(height: 16),
              _section('GET /health', _healthData!),
            ],
            if (_healthDetailed != null) ...[
              const SizedBox(height: 16),
              _section('GET /health/detailed', _healthDetailed!),
            ],
            if (_schedulerConfig != null) ...[
              const SizedBox(height: 16),
              _section('Scheduler config (backend src/tasks/scheduler)', _schedulerConfig!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _section(String title, Map<String, dynamic> data) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...data.entries.map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text('${e.key}: ${e.value}', style: Theme.of(context).textTheme.bodySmall),
                )),
          ],
        ),
      ),
    );
  }
}
