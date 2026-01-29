// Widget tests for Crypto Market app (mirrors backend structure; no counter).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';

void main() {
  testWidgets('App shows Markets tab and navigation', (WidgetTester tester) async {
    await tester.pumpWidget(const CryptoApp());
    await tester.pumpAndSettle();

    expect(find.text('Markets'), findsOneWidget);
  });

  testWidgets('Navigation has Markets, Analytics, Strategy, API Status', (WidgetTester tester) async {
    await tester.pumpWidget(const CryptoApp());
    await tester.pumpAndSettle();

    expect(find.text('Markets'), findsOneWidget);
    expect(find.text('Analytics'), findsOneWidget);
    expect(find.text('Strategy'), findsOneWidget);
    expect(find.text('API Status'), findsOneWidget);
  });
}
