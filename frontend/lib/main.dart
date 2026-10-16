import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'screens/venue_list_screen.dart';

void main() {
  runApp(
    // Show errors immediately (with a Retry button) instead of Riverpod's auto-retry
    ProviderScope(retry: (_, _) => null, child: const WaitWatchApp()),
  );
}

class WaitWatchApp extends StatelessWidget {
  const WaitWatchApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WaitWatch',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      home: const VenueListScreen(),
    );
  }
}
