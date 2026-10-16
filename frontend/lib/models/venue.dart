/// A dining hall with its live average. Mirrors the backend's VenueOut schema.
class Venue {
  const Venue({
    required this.id,
    required this.name,
    required this.lat,
    required this.lng,
    required this.avgWaitMinutes,
    required this.reportCount,
  });

  final int id;
  final String name;
  final double lat;
  final double lng;
  final double? avgWaitMinutes; // null when there are no fresh reports
  final int reportCount;

  factory Venue.fromJson(Map<String, dynamic> json) {
    return Venue(
      id: json['id'] as int,
      name: json['name'] as String,
      // JSON numbers may arrive as int (e.g. 20) or double (e.g. 20.5)
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      avgWaitMinutes: (json['avg_wait_minutes'] as num?)?.toDouble(),
      reportCount: json['report_count'] as int,
    );
  }
}
