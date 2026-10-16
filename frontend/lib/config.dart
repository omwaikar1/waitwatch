/// Where the backend lives.
///
/// Override at build time: flutter run --dart-define=API_BASE_URL=http://...
/// Default: 10.0.2.2 is the Android emulator's alias for the Mac's localhost.
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);
