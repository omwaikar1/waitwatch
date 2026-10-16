import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:waitwatch/api/api_client.dart';
import 'package:waitwatch/models/venue.dart';
import 'package:waitwatch/providers.dart';
import 'package:waitwatch/screens/venue_list_screen.dart';

const sampleVenues = [
  Venue(id: 1, name: 'C4', lat: 42, lng: -75, avgWaitMinutes: 5, reportCount: 1),
  Venue(id: 3, name: 'Hinman Dining', lat: 42, lng: -75, avgWaitMinutes: 25.4, reportCount: 3),
  Venue(id: 5, name: 'Café Tempo', lat: 42, lng: -75, avgWaitMinutes: null, reportCount: 0),
];

/// Builds the screen with venuesProvider replaced by [venues] (no network).
Widget appWith(FutureOr<List<Venue>> Function() venues) {
  return ProviderScope(
    retry: (_, _) => null,
    overrides: [venuesProvider.overrideWith((ref) => venues())],
    child: const MaterialApp(home: VenueListScreen()),
  );
}

void main() {
  testWidgets('shows a spinner while loading', (tester) async {
    final never = Completer<List<Venue>>(); // never completes
    await tester.pumpWidget(appWith(() => never.future));

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('shows every hall with its rounded wait', (tester) async {
    await tester.pumpWidget(appWith(() => sampleVenues));
    await tester.pumpAndSettle();

    expect(find.text('C4'), findsOneWidget);
    expect(find.text('Hinman Dining'), findsOneWidget);
    expect(find.text('25'), findsOneWidget); // 25.4 rounds to 25
    expect(find.text('3 reports in the last 45 min'), findsOneWidget);
    expect(find.text('1 report in the last 45 min'), findsOneWidget); // singular
  });

  testWidgets('hall with no reports shows a dash', (tester) async {
    await tester.pumpWidget(appWith(() => sampleVenues));
    await tester.pumpAndSettle();

    expect(find.text('No recent reports'), findsOneWidget);
    expect(find.text('–'), findsOneWidget);
  });

  testWidgets('error shows the message and Retry reloads', (tester) async {
    var calls = 0;
    await tester.pumpWidget(appWith(() {
      calls++;
      if (calls == 1) throw const ApiException("Can't reach WaitWatch.");
      return sampleVenues;
    }));
    await tester.pumpAndSettle();

    expect(find.text("Can't reach WaitWatch."), findsOneWidget);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.text('Hinman Dining'), findsOneWidget);
  });
}
