import 'package:buddyplan_mobile/models/repeat_settings.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() {
  setUpAll(() => initializeDateFormatting('nl_NL'));

  final monday = DateTime(2026, 11, 2);

  group('summary', () {
    test('describes each repeat type in Dutch', () {
      expect(const RepeatSettings().summary(monday), 'Eenmalig');
      expect(const RepeatSettings(repeatType: 'daily').summary(monday),
          'Dagelijks');
      expect(const RepeatSettings(repeatType: 'weekly').summary(monday),
          'Wekelijks op Maandag');
      expect(const RepeatSettings(repeatType: 'biweekly').summary(monday),
          'Om de 2 weken op Maandag');
      expect(
        const RepeatSettings(repeatType: 'weekdays', repeatWeekdays: [4, 0, 2])
            .summary(monday),
        'Ma, Wo, Vr',
      );
      expect(const RepeatSettings(repeatType: 'weekdays').summary(monday),
          'Op bepaalde dagen');
    });

    test('end summary', () {
      expect(const RepeatSettings().endSummary(), isNull);
      expect(const RepeatSettings(repeatType: 'daily').endSummary(),
          'Geen einddatum');
      expect(
        RepeatSettings(repeatType: 'daily', endDate: DateTime(2026, 12, 31))
            .endSummary(),
        startsWith('Tot 31 dec'),
      );
    });
  });

  group('validate', () {
    test('weekdays needs at least one day', () {
      expect(const RepeatSettings(repeatType: 'weekdays').validate(monday),
          'Selecteer minimaal één dag');
      expect(
          const RepeatSettings(repeatType: 'weekdays', repeatWeekdays: [1])
              .validate(monday),
          isNull);
    });

    test('end date may not be before the start date', () {
      final before =
          RepeatSettings(repeatType: 'daily', endDate: DateTime(2026, 11, 1));
      expect(before.validate(monday),
          'Einddatum moet op of na de startdatum liggen');
      final sameDay = RepeatSettings(
          repeatType: 'daily', endDate: DateTime(2026, 11, 2, 8));
      expect(sameDay.validate(DateTime(2026, 11, 2, 20)), isNull);
    });

    test('end date is ignored for one-off items', () {
      final once = RepeatSettings(endDate: DateTime(2020, 1, 1));
      expect(once.validate(monday), isNull);
    });
  });

  group('API payload', () {
    test(
        'only sends weekdays for the weekdays type and an end date for repeats',
        () {
      expect(
        RepeatSettings(
                repeatType: 'weekly',
                repeatWeekdays: const [1, 2],
                endDate: DateTime(2026, 1, 5))
            .toApiPayload(),
        {
          'repeat_type': 'weekly',
          'repeat_weekdays': <int>[],
          'end_date': '2026-01-05'
        },
      );
      expect(
        RepeatSettings(repeatType: 'once', endDate: DateTime(2026, 1, 5))
            .toApiPayload(),
        {'repeat_type': 'once', 'repeat_weekdays': <int>[]},
      );
      expect(
        const RepeatSettings(repeatType: 'weekdays', repeatWeekdays: [0, 3])
            .toApiPayload(),
        {
          'repeat_type': 'weekdays',
          'repeat_weekdays': [0, 3]
        },
      );
    });

    test('round-trips through the API format', () {
      final parsed = RepeatSettings.fromApi({
        'repeat_type': 'weekdays',
        'repeat_weekdays': [1, 3],
        'end_date': '2026-12-31',
      });
      expect(parsed.repeatType, 'weekdays');
      expect(parsed.repeatWeekdays, [1, 3]);
      expect(parsed.endDate, DateTime(2026, 12, 31));
      expect(parsed.toApiPayload()['end_date'], '2026-12-31');
    });

    test('defaults when fields are missing', () {
      final parsed = RepeatSettings.fromApi({});
      expect(parsed.repeatType, 'once');
      expect(parsed.repeatWeekdays, isEmpty);
      expect(parsed.endDate, isNull);
    });
  });

  test('copyWith can clear the end date', () {
    final settings =
        RepeatSettings(repeatType: 'daily', endDate: DateTime(2026, 12, 31));
    expect(settings.copyWith(clearEndDate: true).endDate, isNull);
    expect(settings.copyWith(repeatType: 'weekly').endDate,
        DateTime(2026, 12, 31));
  });
}
