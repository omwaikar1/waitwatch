import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/venue.dart';
import '../providers.dart';
import 'report_screen.dart';

class VenueListScreen extends ConsumerWidget {
  const VenueListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Rebuilds this screen whenever venuesProvider's state changes
    final venues = ref.watch(venuesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('WaitWatch')),
      body: venues.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _ErrorView(
          message: error.toString(),
          onRetry: () => ref.invalidate(venuesProvider),
        ),
        data: (list) => RefreshIndicator(
          // Pull to refresh: wait for the new data before hiding the spinner
          onRefresh: () => ref.refresh(venuesProvider.future),
          child: ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: list.length,
            itemBuilder: (context, i) => _VenueCard(venue: list[i]),
          ),
        ),
      ),
    );
  }
}

class _VenueCard extends StatelessWidget {
  const _VenueCard({required this.venue});

  final Venue venue;

  @override
  Widget build(BuildContext context) {
    final avg = venue.avgWaitMinutes;
    final textTheme = Theme.of(context).textTheme;

    // Card + InkWell + Row instead of ListTile: ListTile caps the trailing
    // widget's height, which made the badge overflow.
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      clipBehavior: Clip.antiAlias, // keep the tap ripple inside the rounded corners
      child: InkWell(
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(builder: (_) => ReportScreen(venue: venue)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(venue.name, style: textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(
                      avg == null
                          ? 'No recent reports'
                          : '${venue.reportCount} report${venue.reportCount == 1 ? '' : 's'} in the last 45 min',
                      style: textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              _WaitBadge(minutes: avg),
            ],
          ),
        ),
      ),
    );
  }
}

/// The big coloured number on the right of each card.
class _WaitBadge extends StatelessWidget {
  const _WaitBadge({required this.minutes});

  final double? minutes;

  static Color colorFor(double? minutes) {
    if (minutes == null) return Colors.grey;
    if (minutes < 10) return Colors.green;
    if (minutes < 20) return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    final color = colorFor(minutes);
    return Container(
      width: 72,
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            minutes == null ? '–' : minutes!.round().toString(),
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
          ),
          Text('min', style: TextStyle(fontSize: 12, color: color)),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
