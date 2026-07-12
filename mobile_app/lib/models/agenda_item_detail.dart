class AgendaItemDetail {
  final int id;
  final int personId;
  final String title;
  final String source;
  final String repeatType;
  final List<int> repeatWeekdays;
  final DateTime? anchorDate;
  final DateTime? endDate;
  final String? startTime;
  final String? endTime;
  final bool isReadOnly;

  const AgendaItemDetail({
    required this.id,
    required this.personId,
    required this.title,
    required this.source,
    required this.repeatType,
    required this.repeatWeekdays,
    this.anchorDate,
    this.endDate,
    this.startTime,
    this.endTime,
    required this.isReadOnly,
  });

  factory AgendaItemDetail.fromJson(Map<String, dynamic> json) {
    return AgendaItemDetail(
      id: json['id'] as int,
      personId: json['person_id'] as int,
      title: json['title'] as String,
      source: json['source'] as String? ?? 'manual',
      repeatType: json['repeat_type'] as String? ?? 'once',
      repeatWeekdays: (json['repeat_weekdays'] as List<dynamic>?)
              ?.map((e) => e as int)
              .toList() ??
          const [],
      anchorDate: json['anchor_date'] != null
          ? DateTime.parse(json['anchor_date'] as String)
          : null,
      endDate: json['end_date'] != null
          ? DateTime.parse(json['end_date'] as String)
          : null,
      startTime: json['start_time'] as String?,
      endTime: json['end_time'] as String?,
      isReadOnly: json['is_read_only'] as bool? ??
          (json['source'] == 'ical' || json['source'] == 'gcal'),
    );
  }

  String get sourceLabel {
    switch (source) {
      case 'ical':
        return 'iCal-feed';
      case 'gcal':
        return 'Google Agenda';
      default:
        return 'Handmatig';
    }
  }
}
