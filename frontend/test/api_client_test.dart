import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:waitwatch/api/api_client.dart';

/// Replaces Dio's network layer: returns a canned response, records the request.
class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.status, this.body, {this.headers = const {}, this.throwError});

  final int status;
  final Object? body;
  final Map<String, List<String>> headers;
  final DioExceptionType? throwError;
  RequestOptions? lastRequest;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastRequest = options;
    if (throwError != null) {
      throw DioException(requestOptions: options, type: throwError!);
    }
    return ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        'content-type': ['application/json'],
        ...headers,
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

ApiClient clientWith(FakeAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
  return ApiClient(dio);
}

void main() {
  test('getVenues parses the list', () async {
    final client = clientWith(FakeAdapter(200, [
      {'id': 1, 'name': 'C4', 'lat': 42.0, 'lng': -75.0, 'avg_wait_minutes': 12.0, 'report_count': 3},
    ]));

    final venues = await client.getVenues();

    expect(venues.single.name, 'C4');
    expect(venues.single.avgWaitMinutes, 12.0);
  });

  test('submitReport sends the right path and body', () async {
    final adapter = FakeAdapter(201, {'id': 1});
    await clientWith(adapter).submitReport(venueId: 3, deviceId: 'abc', minutes: 15);

    expect(adapter.lastRequest!.method, 'POST');
    expect(adapter.lastRequest!.path, '/venues/3/reports');
    expect(adapter.lastRequest!.data, {'device_id': 'abc', 'wait_minutes': 15});
  });

  test('429 becomes "report again in N min" using Retry-After', () async {
    final client = clientWith(FakeAdapter(429, {'detail': 'x'}, headers: {
      'retry-after': ['420'],
    }));

    expect(
      () => client.submitReport(venueId: 1, deviceId: 'abc', minutes: 10),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', contains('7 min'))),
    );
  });

  test('429 rounds partial minutes up', () async {
    final client = clientWith(FakeAdapter(429, {}, headers: {
      'retry-after': ['61'],
    }));

    expect(
      () => client.submitReport(venueId: 1, deviceId: 'abc', minutes: 10),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', contains('2 min'))),
    );
  });

  test('404 becomes a friendly message', () async {
    final client = clientWith(FakeAdapter(404, {'detail': 'Venue not found'}));

    expect(
      () => client.submitReport(venueId: 999, deviceId: 'abc', minutes: 10),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', contains('no longer exists'))),
    );
  });

  test('no connection becomes "Can\'t reach WaitWatch"', () async {
    final client = clientWith(FakeAdapter(0, null, throwError: DioExceptionType.connectionTimeout));

    expect(
      client.getVenues,
      throwsA(isA<ApiException>().having((e) => e.message, 'message', contains("Can't reach"))),
    );
  });
}
