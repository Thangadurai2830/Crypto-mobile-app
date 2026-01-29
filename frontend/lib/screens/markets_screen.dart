import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/models.dart';
import '../services/services.dart';
import '../utils/utils.dart';
import 'market_detail_screen.dart';

/// Markets list: card-style rows with circular avatar, name, ticker, price, volume.
class MarketsScreen extends StatefulWidget {
  const MarketsScreen({super.key});

  @override
  State<MarketsScreen> createState() => _MarketsScreenState();
}

class _MarketsScreenState extends State<MarketsScreen> {
  final DataIngestionService _ingestion = DataIngestionService();
  final MarketService _market = MarketService();
  List<MarketAsset> _markets = [];
  String? _error;
  bool _loading = true;
  bool _ingesting = false;

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
      final list = await _market.listMarkets();
      setState(() {
        _markets = list;
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

  Future<void> _triggerIngest() async {
    setState(() => _ingesting = true);
    try {
      final list = await _ingestion.triggerIngestAndRefreshMarkets();
      setState(() => _markets = list);
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ingest: ${e.message}')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ingest: $e')));
    }
    if (mounted) setState(() => _ingesting = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Markets', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
        backgroundColor: AppTheme.background,
        actions: [
          IconButton(
            icon: _ingesting
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary))
                : const Icon(Icons.cloud_download, color: AppTheme.textPrimary),
            onPressed: _ingesting ? null : _triggerIngest,
            tooltip: 'Trigger ingest',
          ),
          IconButton(icon: const Icon(Icons.refresh, color: AppTheme.textPrimary), onPressed: _loading ? null : _load, tooltip: 'Refresh'),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 48, color: AppTheme.negative),
              const SizedBox(height: 16),
              Text('Could not load markets', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Text(_error!, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(height: 24),
              FilledButton.icon(onPressed: _load, icon: const Icon(Icons.refresh), label: const Text('Retry')),
            ],
          ),
        ),
      );
    }
    if (_markets.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('No market data. Trigger ingest to fetch from API.', style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 16),
            FilledButton.icon(onPressed: _triggerIngest, icon: const Icon(Icons.cloud_download), label: const Text('Trigger ingest')),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      color: AppTheme.primary,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        itemCount: _markets.length,
        itemBuilder: (context, i) {
          final a = _markets[i];
          return _MarketCard(
            asset: a,
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (context) => MarketDetailScreen(symbol: a.symbol),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _MarketCard extends StatelessWidget {
  const _MarketCard({required this.asset, required this.onTap});

  final MarketAsset asset;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final price = asset.latestPrice;
    final vol = asset.latestVolume;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Material(
        color: AppTheme.card,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 24,
                  backgroundColor: AppTheme.avatarTint,
                  child: Text(
                    asset.symbol.substring(0, 1).toUpperCase(),
                    style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(asset.name ?? asset.symbol, style: Theme.of(context).textTheme.titleSmall),
                      const SizedBox(height: 2),
                      Text(asset.symbol, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    if (price != null) Text(formatPrice(price, decimals: 2), style: Theme.of(context).textTheme.titleSmall),
                    if (vol != null) Text('Vol: ${formatVolume(vol)}', style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
