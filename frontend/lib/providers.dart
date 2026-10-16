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
      // 10s, not 5s: a phone on weak signal (or just waking up) can need more than
      // 5s for the first DNS + TCP + TLS connection to the live server.
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
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
