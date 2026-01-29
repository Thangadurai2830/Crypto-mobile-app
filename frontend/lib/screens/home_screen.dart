import 'package:flutter/material.dart';

import '../core/app_theme.dart';
import '../models/models.dart';
import '../services/services.dart';
import '../utils/utils.dart';
import 'market_detail_screen.dart';

/// Portfolio/Home screen matching Figma: balance, quick actions, alerts, holdings list.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MarketService _market = MarketService();
  List<MarketAsset> _holdings = [];
  String? _error;
  bool _loading = true;

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
        _holdings = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  /// Placeholder balance (sum of first 5 assets * 1000 for demo).
  double get _balance {
    if (_holdings.isEmpty) return 15320.45;
    double sum = 0;
    for (var i = 0; i < _holdings.length && i < 5; i++) {
      final p = _holdings[i].latestPrice ?? 0;
      sum += p * 1000;
    }
    return sum > 0 ? sum : 15320.45;
  }

  double get _change => 5320.45;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _load,
          color: AppTheme.primary,
          child: CustomScrollView(
            slivers: [
              _buildHeader(),
              SliverToBoxAdapter(child: _buildBalance()),
              SliverToBoxAdapter(child: _buildQuickActions()),
              SliverToBoxAdapter(child: _buildAlerts()),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                  child: Text('Holdings', style: Theme.of(context).textTheme.titleLarge),
                ),
              ),
              _buildHoldingsList(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return SliverToBoxAdapter(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        child: Row(
          children: [
            CircleAvatar(
              radius: 22,
              backgroundColor: AppTheme.card,
              child: const Text('M', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 18)),
            ),
            const Expanded(
              child: Center(
                child: Text('My Portfolio', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 20)),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.notifications_none, color: AppTheme.textPrimary),
              onPressed: () {},
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBalance() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(formatCurrency(_balance), style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(height: 4),
          Text('+${formatCurrency(_change)}', style: const TextStyle(color: AppTheme.positive, fontWeight: FontWeight.w600, fontSize: 16)),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    const actions = [
      _QuickAction(icon: Icons.arrow_upward, label: 'Deposit'),
      _QuickAction(icon: Icons.arrow_downward, label: 'Withdraw'),
      _QuickAction(icon: Icons.send, label: 'Send'),
      _QuickAction(icon: Icons.download, label: 'Receive'),
    ];
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: actions.map((a) => _buildActionButton(a)).toList(),
      ),
    );
  }

  Widget _buildActionButton(_QuickAction a) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Material(
          color: AppTheme.card,
          shape: const CircleBorder(),
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: () {},
            child: SizedBox(width: 56, height: 56, child: Icon(a.icon, color: AppTheme.textPrimary)),
          ),
        ),
        const SizedBox(height: 8),
        Text(a.label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
      ],
    );
  }

  Widget _buildAlerts() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Alerts', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(color: AppTheme.card, borderRadius: BorderRadius.circular(12)),
            child: Row(
              children: [
                const Icon(Icons.notifications_none, color: AppTheme.primary, size: 24),
                const SizedBox(width: 12),
                Expanded(child: Text('Bitcoin price reached \$20,000', style: Theme.of(context).textTheme.bodyMedium)),
                Text('5min ago', style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHoldingsList() {
    if (_loading) {
      return const SliverFillRemaining(child: Center(child: CircularProgressIndicator(color: AppTheme.primary)));
    }
    if (_error != null) {
      return SliverFillRemaining(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppTheme.textSecondary)),
              const SizedBox(height: 16),
              TextButton(onPressed: _load, child: const Text('Retry')),
            ],
          ),
        ),
      );
    }
    if (_holdings.isEmpty) {
      return SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Center(child: Text('No holdings. Check Markets.', style: Theme.of(context).textTheme.bodyMedium)),
        ),
      );
    }
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      sliver: SliverList(
        delegate: SliverChildBuilderDelegate(
          (context, i) {
            final a = _holdings[i];
            final price = a.latestPrice;
            final value = price != null ? (price * 1000).toDouble() : 0.0;
            final change = (i % 3 == 0) ? 3.5 : (i % 3 == 1 ? -2.3 : 0.0);
            return _HoldingsTile(
              asset: a,
              value: value,
              changePercent: change,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => MarketDetailScreen(symbol: a.symbol),
                ),
              ),
            );
          },
          childCount: _holdings.length,
        ),
      ),
    );
  }
}

class _QuickAction {
  const _QuickAction({required this.icon, required this.label});
  final IconData icon;
  final String label;
}

class _HoldingsTile extends StatelessWidget {
  const _HoldingsTile({
    required this.asset,
    required this.value,
    required this.changePercent,
    required this.onTap,
  });

  final MarketAsset asset;
  final double value;
  final double changePercent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isPositive = changePercent >= 0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: AppTheme.card,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 22,
                  backgroundColor: AppTheme.avatarTint,
                  child: Text(
                    asset.symbol.substring(0, 1).toUpperCase(),
                    style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(asset.name ?? asset.symbol, style: Theme.of(context).textTheme.titleSmall),
                      Text(asset.symbol, style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(formatCurrency(value), style: Theme.of(context).textTheme.titleSmall),
                    Text(
                      '${isPositive ? '+' : ''}${changePercent.toStringAsFixed(1)}%',
                      style: TextStyle(color: isPositive ? AppTheme.positive : AppTheme.negative, fontSize: 12),
                    ),
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
