import 'dart:async';

import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/models.dart';
import '../services/services.dart';
import '../utils/utils.dart';

/// Asset detail screen matching Figma: header, price, 24h change, chart, timeframes, overview, Buy/Sell.
class MarketDetailScreen extends StatefulWidget {
  const MarketDetailScreen({super.key, required this.symbol});

  final String symbol;

  @override
  State<MarketDetailScreen> createState() => _MarketDetailScreenState();
}

class _MarketDetailScreenState extends State<MarketDetailScreen> {
  final MarketService _market = MarketService();
  MarketAsset? _asset;
  PriceRecord? _currentPrice;
  List<PriceRecord> _history = [];
  PriceRecord? _livePrice;
  StreamSubscription<PriceRecord>? _wsSub;
  String? _error;
  bool _loading = true;
  int _selectedTimeframe = 1; // 0=1H, 1=24H, 2=1W, 3=1M, 4=1Y, 5=ALL

  static const List<String> _timeframes = ['1H', '24H', '1W', '1M', '1Y', 'ALL'];

  @override
  void initState() {
    super.initState();
    _load();
    _connectLive();
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final asset = await _market.getMarket(widget.symbol);
      final price = await _market.getCurrentPrice(widget.symbol);
      final history = await _market.getHistory(widget.symbol, limit: 100);
      setState(() {
        _asset = asset;
        _currentPrice = price;
        _history = history;
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

  void _connectLive() {
    _wsSub?.cancel();
    _wsSub = _market.streamPriceUpdates(widget.symbol).listen(
      (record) {
        if (mounted) setState(() => _livePrice = record);
      },
      onError: (_) {},
    );
  }

  /// Placeholder 24h change (demo).
  double get _change24h => 3.5;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: AppTheme.textPrimary, size: 20),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: AppTheme.avatarTint,
              child: Text(
                widget.symbol.substring(0, 1).toUpperCase(),
                style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 14),
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(_asset?.name ?? widget.symbol, style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 16)),
                Text(widget.symbol, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
              ],
            ),
          ],
        ),
        centerTitle: true,
        actions: [
          IconButton(icon: const Icon(Icons.star_border, color: AppTheme.textPrimary), onPressed: () {}),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: _buildBottomActions(),
    );
  }

  Widget _buildBody() {
    if (_loading && _asset == null) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.primary));
    }
    if (_error != null && _asset == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textSecondary)),
              const SizedBox(height: 16),
              FilledButton(onPressed: _load, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }
    final price = _livePrice ?? _currentPrice;
    return RefreshIndicator(
      onRefresh: _load,
      color: AppTheme.primary,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (price != null) ...[
              const SizedBox(height: 16),
              Text(formatPrice(price.price, decimals: 2), style: Theme.of(context).textTheme.headlineLarge),
              const SizedBox(height: 4),
              Text(
                '+${_change24h.toStringAsFixed(1)}% (24h)',
                style: const TextStyle(color: AppTheme.positive, fontWeight: FontWeight.w600, fontSize: 16),
              ),
            ],
            const SizedBox(height: 24),
            _buildChart(),
            const SizedBox(height: 20),
            _buildTimeframeChips(),
            const SizedBox(height: 24),
            _buildOverview(),
            const SizedBox(height: 100),
          ],
        ),
      ),
    );
  }

  Widget _buildChart() {
    if (_history.isEmpty) {
      return Container(
        height: 200,
        decoration: BoxDecoration(color: AppTheme.card, borderRadius: BorderRadius.circular(12)),
        child: const Center(child: Text('No chart data', style: TextStyle(color: AppTheme.textSecondary))),
      );
    }
    return Container(
      height: 200,
      decoration: BoxDecoration(color: AppTheme.card, borderRadius: BorderRadius.circular(12)),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: CustomPaint(
          size: const Size(double.infinity, 200),
          painter: _LineChartPainter(records: _history),
        ),
      ),
    );
  }

  Widget _buildTimeframeChips() {
    return Row(
      children: List.generate(_timeframes.length, (i) {
        final selected = i == _selectedTimeframe;
        return Padding(
          padding: const EdgeInsets.only(right: 8),
          child: Material(
            color: selected ? AppTheme.primary : AppTheme.card,
            borderRadius: BorderRadius.circular(8),
            child: InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: () => setState(() => _selectedTimeframe = i),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Text(
                  _timeframes[i],
                  style: TextStyle(
                    color: selected ? Colors.black : AppTheme.textPrimary,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                    fontSize: 13,
                  ),
                ),
              ),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildOverview() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Overview', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: AppTheme.card, borderRadius: BorderRadius.circular(12)),
          child: Text(
            _asset?.name != null
                ? '${_asset!.name} (${widget.symbol}) — current price and volume from the backend. Historical data shown in the chart above.'
                : 'Lorem ipsum dolor sit amet consectetur.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ),
      ],
    );
  }

  Widget _buildBottomActions() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 12),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () {},
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  side: const BorderSide(color: AppTheme.textSecondary),
                ),
                child: const Text('Sell', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600)),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: FilledButton(
                onPressed: () {},
                style: FilledButton.styleFrom(
                  backgroundColor: AppTheme.primary,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Buy', style: TextStyle(fontWeight: FontWeight.w600)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Simple line chart from price history.
class _LineChartPainter extends CustomPainter {
  _LineChartPainter({required this.records});

  final List<PriceRecord> records;

  @override
  void paint(Canvas canvas, Size size) {
    if (records.isEmpty) return;
    final prices = records.map((r) => r.price.toDouble()).toList();
    final minP = prices.reduce((a, b) => a < b ? a : b);
    final maxP = prices.reduce((a, b) => a > b ? a : b);
    final range = (maxP - minP).clamp(0.01, double.infinity);
    const pad = 16.0;
    final w = size.width - pad * 2;
    final h = size.height - pad * 2;
    final path = Path();
    for (var i = 0; i < prices.length; i++) {
      final x = pad + (i / (prices.length - 1).clamp(1, double.infinity)) * w;
      final y = pad + h - ((prices[i] - minP) / range) * h;
      if (i == 0) path.moveTo(x, y);
      else path.lineTo(x, y);
    }
    final fillPath = Path.from(path)
      ..lineTo(pad + w, size.height - pad)
      ..lineTo(pad, size.height - pad)
      ..close();
    final fillPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [AppTheme.primary.withOpacity(0.3), AppTheme.primary.withOpacity(0.0)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawPath(fillPath, fillPaint);
    final linePaint = Paint()
      ..color = AppTheme.primary
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(path, linePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
