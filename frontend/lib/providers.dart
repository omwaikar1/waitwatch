import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import 'api/api_client.dart';
import 'config.dart';
import 'models/venue.dart';

/// One configured HTTP client for the whole app.
final dioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 5),
    ),
  );
});

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(dioProvider));
});

/// This phone's anonymous ID (DECISIONS #3). Created on first launch, then reused
/// forever, so the backend's rate limit really is per device.
final deviceIdProvider = FutureProvider<String>((ref) async {
  const key = 'device_id';
  final prefs = await SharedPreferences.getInstance();
  final existing = prefs.getString(key);
  if (existing != null) return existing;

  final created = const Uuid().v4();
  await prefs.setString(key, created);
  return created;
});

/// All halls with their live averages. Refresh with ref.refresh / ref.invalidate.
final venuesProvider = FutureProvider<List<Venue>>((ref) {
  return ref.watch(apiClientProvider).getVenues();
});
