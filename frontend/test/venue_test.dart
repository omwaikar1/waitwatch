import 'package:flutter_test/flutter_test.dart';
import 'package:waitwatch/models/venue.dart';

void main() {
  test('parses a venue with an average', () {
    final venue = Venue.fromJson({
      'id': 3,
      'name': 'Hinman Dining',
      'lat': 42.0925,
      'lng': -75.9685,
      'avg_wait_minutes': 15.5,
      'report_count': 2,
    });

    expect(venue.id, 3);
    expect(venue.name, 'Hinman Dining');
    expect(venue.avgWaitMinutes, 15.5);
    expect(venue.reportCount, 2);
  });

  test('null average means no recent reports', () {
    final venue = Venue.fromJson({
      'id': 1,
      'name': 'C4',
      'lat': 42,
      'lng': -75,
      'avg_wait_minutes': null,
      'report_count': 0,
    });

    expect(venue.avgWaitMinutes, isNull);
  });

  test('whole-number JSON values become doubles', () {
    // The backend can send 20 (int) instead of 20.0 for an average
    final venue = Venue.fromJson({
      'id': 1,
      'name': 'C4',
      'lat': 42,
      'lng': -75,
      'avg_wait_minutes': 20,
      'report_count': 2,
    });

    expect(venue.avgWaitMinutes, 20.0);
    expect(venue.lat, 42.0);
  });
}
