import 'package:flutter/material.dart';

import 'core/app_theme.dart';
import 'screens/analytics_screen.dart';
import 'screens/health_screen.dart';
import 'screens/home_screen.dart';
import 'screens/markets_screen.dart';
import 'screens/strategy_screen.dart';

void main() {
  runApp(const CryptoApp());
}

class CryptoApp extends StatelessWidget {
  const CryptoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Crypto App',
      theme: AppTheme.dark,
      debugShowCheckedModeBanner: false,
      home: const CryptoMainShell(),
    );
  }
}

class CryptoMainShell extends StatefulWidget {
  const CryptoMainShell({super.key});

  @override
  State<CryptoMainShell> createState() => _CryptoMainShellState();
}

class _CryptoMainShellState extends State<CryptoMainShell> {
  int _navIndex = 0;

  static const List<_NavItem> _navItems = [
    _NavItem(icon: Icons.home_rounded, label: 'Home'),
    _NavItem(icon: Icons.list_rounded, label: 'Markets'),
    _NavItem(icon: Icons.analytics_rounded, label: 'Analytics'),
    _NavItem(icon: Icons.trending_up_rounded, label: 'Strategy'),
    _NavItem(icon: Icons.health_and_safety_rounded, label: 'API Status'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _navIndex,
        children: const [
          HomeScreen(),
          MarketsScreen(),
          AnalyticsScreen(),
          StrategyScreen(),
          HealthScreen(),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: AppTheme.surface,
          border: Border(top: BorderSide(color: AppTheme.card, width: 1)),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
            child: Row(
              children: List.generate(_navItems.length, (i) {
                final item = _navItems[i];
                final selected = i == _navIndex;
                return Expanded(
                  child: _NavBarItem(
                    icon: item.icon,
                    label: item.label,
                    selected: selected,
                    onTap: () => setState(() => _navIndex = i),
                  ),
                );
              }),
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem({required this.icon, required this.label});
  final IconData icon;
  final String label;
}

class _NavBarItem extends StatelessWidget {
  const _NavBarItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppTheme.primary : AppTheme.textSecondary;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 22, color: color),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(color: color, fontSize: 10, fontWeight: selected ? FontWeight.w600 : FontWeight.normal),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
