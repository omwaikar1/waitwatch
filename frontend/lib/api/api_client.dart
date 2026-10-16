import 'package:dio/dio.dart';

import '../models/venue.dart';

/// An API failure with a message that's safe to show to the user.
class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// The only place in the app that talks HTTP to the backend.
class ApiClient {
  ApiClient(this._dio);

  final Dio _dio;

  Future<bool> checkHealth() => _call(() async {
        final response = await _dio.get<Map<String, dynamic>>('/health');
        return response.data?['status'] == 'ok';
      });

  Future<List<Venue>> getVenues() => _call(() async {
        final response = await _dio.get<List<dynamic>>('/venues');
        return response.data!
            .map((json) => Venue.fromJson(json as Map<String, dynamic>))
            .toList();
      });

  Future<void> submitReport({
    required int venueId,
    required String deviceId,
    required int minutes,
  }) =>
      _call(() async {
        await _dio.post<void>(
          '/venues/$venueId/reports',
          data: {'device_id': deviceId, 'wait_minutes': minutes},
        );
      });

  /// Runs a request and turns any Dio error into a friendly ApiException.
  Future<T> _call<T>(Future<T> Function() request) async {
    try {
      return await request();
    } on DioException catch (e) {
      throw ApiException(_messageFor(e));
    }
  }

  static String _messageFor(DioException e) {
    final response = e.response;
    if (response == null) {
      // Timeout, refused connection, no network…
      return "Can't reach WaitWatch. Check your connection and try again.";
    }
    switch (response.statusCode) {
      case 429:
        final seconds = int.tryParse(response.headers.value('retry-after') ?? '') ?? 600;
        final minutes = (seconds / 60).ceil();
        return 'You already reported this hall. You can report again in $minutes min.';
      case 404:
        return 'That dining hall no longer exists.';
      case 422:
        return 'Wait time must be between 0 and 120 minutes.';
      default:
        return 'Something went wrong (${response.statusCode}). Please try again.';
    }
  }
}
