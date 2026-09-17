class CalendarEvent {
  final int id;
  final String title;
  final int personId;
  final DateTime date;
  final String? startTime;
  final String? endTime;
  final String source;

  const CalendarEvent({
    required this.id,
    required this.title,
    required this.personId,
    required this.date,
    this.startTime,
    this.endTime,
    this.source = 'manual',
  });

  bool get isFeedSynced => source == 'ical' || source == 'gcal';

  /// Compact time label for list/chip UIs (`09:00` or `09:00–10:30`).
  String? get timeRangeLabel {
    if (startTime != null && endTime != null) return '$startTime–$endTime';
    return startTime ?? endTime;
  }

  /// Display label for compact chips (month); includes times when present.
  String get displayText {
    final time = timeRangeLabel;
    return time == null ? title : '$time $title';
  }

  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    return CalendarEvent(
      id: json['id'] as int,
      title: json['title'] as String,
      personId: json['person_id'] as int,
      date: DateTime.parse(json['date'] as String),
      startTime: json['start_time'] as String?,
      endTime: json['end_time'] as String?,
      source: json['source'] as String? ?? 'manual',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'person_id': personId,
        'date': date.toIso8601String().split('T').first,
        if (startTime != null) 'start_time': startTime,
        if (endTime != null) 'end_time': endTime,
        'source': source,
      };
}
