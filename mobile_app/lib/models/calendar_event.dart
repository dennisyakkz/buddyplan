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

  /// Display label shown in calendar chips/tiles (server applies feed rules).
  String get displayText => title;

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
