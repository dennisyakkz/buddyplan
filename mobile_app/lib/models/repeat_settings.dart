import 'package:intl/intl.dart';

const List<String> weekdayShortLabels = [
  'Ma',
  'Di',
  'Wo',
  'Do',
  'Vr',
  'Za',
  'Zo',
];

const List<String> weekdayFullLabels = [
  'Maandag',
  'Dinsdag',
  'Woensdag',
  'Donderdag',
  'Vrijdag',
  'Zaterdag',
  'Zondag',
];

const List<(String value, String label)> repeatTypeOptions = [
  ('once', 'Eenmalig'),
  ('daily', 'Dagelijks'),
  ('weekly', 'Wekelijks'),
  ('biweekly', 'Om de 2 weken'),
  ('weekdays', 'Op bepaalde dagen'),
];

class RepeatSettings {
  final String repeatType;
  final List<int> repeatWeekdays;
  final DateTime? endDate;

  const RepeatSettings({
    this.repeatType = 'once',
    this.repeatWeekdays = const [],
    this.endDate,
  });

  RepeatSettings copyWith({
    String? repeatType,
    List<int>? repeatWeekdays,
    DateTime? endDate,
    bool clearEndDate = false,
  }) {
    return RepeatSettings(
      repeatType: repeatType ?? this.repeatType,
      repeatWeekdays: repeatWeekdays ?? this.repeatWeekdays,
      endDate: clearEndDate ? null : (endDate ?? this.endDate),
    );
  }

  Map<String, dynamic> toApiPayload() {
    return {
      'repeat_type': repeatType,
      'repeat_weekdays': repeatType == 'weekdays' ? repeatWeekdays : <int>[],
      if (endDate != null && repeatType != 'once')
        'end_date': _isoDate(endDate!),
    };
  }

  String summary(DateTime anchorDate) {
    switch (repeatType) {
      case 'daily':
        return 'Dagelijks';
      case 'weekly':
        return 'Wekelijks op ${weekdayFullLabels[_weekdayIndex(anchorDate)]}';
      case 'biweekly':
        return 'Om de 2 weken op ${weekdayFullLabels[_weekdayIndex(anchorDate)]}';
      case 'weekdays':
        if (repeatWeekdays.isEmpty) return 'Op bepaalde dagen';
        final sorted = List<int>.from(repeatWeekdays)..sort();
        return sorted.map((d) => weekdayShortLabels[d]).join(', ');
      case 'once':
      default:
        return 'Eenmalig';
    }
  }

  String? endSummary() {
    if (repeatType == 'once') return null;
    if (endDate == null) return 'Geen einddatum';
    return 'Tot ${DateFormat('d MMM yyyy', 'nl_NL').format(endDate!)}';
  }

  String? validate(DateTime anchorDate) {
    if (repeatType == 'weekdays' && repeatWeekdays.isEmpty) {
      return 'Selecteer minimaal één dag';
    }
    if (endDate != null && repeatType != 'once') {
      final anchor = DateTime(anchorDate.year, anchorDate.month, anchorDate.day);
      final end = DateTime(endDate!.year, endDate!.month, endDate!.day);
      if (end.isBefore(anchor)) {
        return 'Einddatum moet op of na de startdatum liggen';
      }
    }
    return null;
  }

  static int _weekdayIndex(DateTime date) => date.weekday - 1;

  static String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  factory RepeatSettings.fromApi(Map<String, dynamic> json) {
    DateTime? endDate;
    final endRaw = json['end_date'] as String?;
    if (endRaw != null) {
      endDate = DateTime.parse(endRaw);
    }
    return RepeatSettings(
      repeatType: json['repeat_type'] as String? ?? 'once',
      repeatWeekdays: (json['repeat_weekdays'] as List<dynamic>?)
              ?.map((e) => e as int)
              .toList() ??
          const [],
      endDate: endDate,
    );
  }
}
