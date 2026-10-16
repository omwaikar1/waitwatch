import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:waitwatch/api/api_client.dart';
import 'package:waitwatch/models/venue.dart';
import 'package:waitwatch/providers.dart';
import 'package:waitwatch/screens/report_screen.dart';

const hinman = Venue(id: 3, name: 'Hinman Dining', lat: 42, lng: -75, avgWaitMinutes: null, reportCount: 0);

/// Records submitReport calls instead of sending HTTP. Optionally fails.
class FakeApiClient extends ApiClient {
  FakeApiClient({this.failWith}) : super(Dio());

  final ApiException? failWith;
  final submitted = <({int venueId, String deviceId, int minutes})>[];

  @override
  Future<void> submitReport({required int venueId, required String deviceId, required int minutes}) async {
    if (failWith != null) throw failWith!;
    submitted.add((venueId: venueId, deviceId: deviceId, minutes: minutes));
  }
}

/// A home screen with an "open" button, so ReportScreen has something to pop back to.
Widget appWith(FakeApiClient api) {
  return ProviderScope(
    retry: (_, _) => null,
    overrides: [
      apiClientProvider.overrideWithValue(api),
      deviceIdProvider.overrideWith((ref) async => 'test-device'),
      venuesProvider.overrideWith((ref) async => const <Venue>[]),
    ],
    child: MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          body: TextButton(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => const ReportScreen(venue: hinman)),
            ),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );
}

Future<void> openReportScreen(WidgetTester tester, FakeApiClient api) async {
  await tester.pumpWidget(appWith(api));
  await tester.tap(find.text('open'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows the hall name and a 10 min default', (tester) async {
    await openReportScreen(tester, FakeApiClient());

    expect(find.text('Hinman Dining'), findsOneWidget);
    expect(find.text('10 min'), findsOneWidget);
  });

  testWidgets('tapping a quick pick changes the value', (tester) async {
    await openReportScreen(tester, FakeApiClient());

    await tester.tap(find.widgetWithText(ChoiceChip, '30'));
    await tester.pump();

    expect(find.text('30 min'), findsOneWidget);
  });

  testWidgets('submit sends the picked minutes with the device id, then closes', (tester) async {
    final api = FakeApiClient();
    await openReportScreen(tester, api);

    await tester.tap(find.widgetWithText(ChoiceChip, '15'));
    await tester.tap(find.text('Submit report'));
    await tester.pumpAndSettle();

    expect(api.submitted, [(venueId: 3, deviceId: 'test-device', minutes: 15)]);
    expect(find.text('Thanks! Your report is in.'), findsOneWidget);
    expect(find.byType(ReportScreen), findsNothing); // popped back
  });

  testWidgets('an API error is shown and the screen stays open', (tester) async {
    final api = FakeApiClient(failWith: const ApiException('You can report again in 7 min.'));
    await openReportScreen(tester, api);

    await tester.tap(find.text('Submit report'));
    await tester.pumpAndSettle();

    expect(find.text('You can report again in 7 min.'), findsOneWidget);
    expect(find.byType(ReportScreen), findsOneWidget);
    // Button is usable again after the failure
    expect(tester.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNotNull);
  });
}
