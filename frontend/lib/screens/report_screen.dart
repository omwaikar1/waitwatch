import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import '../models/venue.dart';
import '../providers.dart';

class ReportScreen extends ConsumerStatefulWidget {
  const ReportScreen({super.key, required this.venue});

  final Venue venue;

  @override
  ConsumerState<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends ConsumerState<ReportScreen> {
  // One tap while standing in line; the slider covers anything else
  static const quickPicks = [0, 5, 10, 15, 20, 30, 45, 60];

  int _minutes = 10;
  bool _submitting = false;

  Future<void> _submit() async {
    setState(() => _submitting = true);
    final messenger = ScaffoldMessenger.of(context); // grab before any await
    final navigator = Navigator.of(context);

    try {
      final deviceId = await ref.read(deviceIdProvider.future);
      await ref.read(apiClientProvider).submitReport(
            venueId: widget.venue.id,
            deviceId: deviceId,
            minutes: _minutes,
          );
      ref.invalidate(venuesProvider); // list refetches with the new average
      messenger.showSnackBar(const SnackBar(content: Text('Thanks! Your report is in.')));
      navigator.pop();
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.message)));
      if (mounted) setState(() => _submitting = false); // screen may have closed
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(title: Text(widget.venue.name)),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text('How long is the wait right now?', style: textTheme.titleMedium),
          const SizedBox(height: 24),
          Center(
            child: Text(
              '$_minutes min',
              style: textTheme.displayMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              for (final m in quickPicks)
                ChoiceChip(
                  label: Text('$m'),
                  selected: _minutes == m,
                  onSelected: _submitting ? null : (_) => setState(() => _minutes = m),
                ),
            ],
          ),
          const SizedBox(height: 16),
          Slider(
            value: _minutes.toDouble(),
            max: 120,
            divisions: 120,
            label: '$_minutes min',
            onChanged: _submitting ? null : (v) => setState(() => _minutes = v.round()),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _submitting ? null : _submit,
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(52)),
            child: _submitting
                ? const SizedBox.square(
                    dimension: 22,
                    child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white),
                  )
                : const Text('Submit report'),
          ),
        ],
      ),
    );
  }
}
