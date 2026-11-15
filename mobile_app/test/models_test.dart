import 'package:buddyplan_mobile/core/auth_exception.dart';
import 'package:buddyplan_mobile/core/network_utils.dart';
import 'package:buddyplan_mobile/models/calendar_event.dart';
import 'package:buddyplan_mobile/models/task_item.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CalendarEvent', () {
    final json = {
      'id': 5,
      'title': 'Zwemles',
      'person_id': 2,
      'date': '2026-11-02',
      'start_time': '16:00',
      'end_time': '17:00',
      'source': 'ical',
    };

    test('parses the /api/mobile/calendar format and serializes it back', () {
      final event = CalendarEvent.fromJson(json);
      expect(event.date, DateTime(2026, 11, 2));
      expect(event.isFeedSynced, isTrue);
      expect(event.toJson(), json);
    });

    test('time labels', () {
      final event = CalendarEvent.fromJson(json);
      expect(event.timeRangeLabel, '16:00–17:00');
      expect(event.displayText, '16:00–17:00 Zwemles');

      final allDay = CalendarEvent.fromJson({
        'id': 1,
        'title': 'Studiedag',
        'person_id': 2,
        'date': '2026-11-05'
      });
      expect(allDay.timeRangeLabel, isNull);
      expect(allDay.displayText, 'Studiedag');
      expect(allDay.source, 'manual');
      expect(allDay.isFeedSynced, isFalse);
    });
  });

  test('TaskItem fills in defaults for optional fields', () {
    final task = TaskItem.fromJson(
        {'id': '7-2026-11-02', 'title': 'Afwassen', 'date': '2026-11-02'});
    expect(task.description, '');
    expect(task.icon, 'md:check_circle');
    expect(task.personId, isNull);
    expect(task.completed, isFalse);
    expect(task.toJson()['date'], '2026-11-02');
  });

  group('error messages', () {
    final options = RequestOptions(path: '/api/tasks');

    test('auth errors ask to log in again', () {
      expect(isAuthError(const AuthRequiredException()), isTrue);
      expect(friendlyErrorMessage(const AuthRequiredException()),
          'Sessie verlopen. Log opnieuw in.');
    });

    test('connection problems are network errors', () {
      final timeout = DioException(
          requestOptions: options, type: DioExceptionType.connectionTimeout);
      expect(isNetworkError(timeout), isTrue);
      expect(friendlyErrorMessage(timeout),
          startsWith('Geen verbinding met de server'));
    });

    test('server errors show the Dutch detail from the backend', () {
      final error = DioException(
        requestOptions: options,
        type: DioExceptionType.badResponse,
        response: Response(
            requestOptions: options,
            statusCode: 400,
            data: {'detail': 'Naam is verplicht'}),
      );
      expect(isNetworkError(error), isFalse);
      expect(friendlyErrorMessage(error), 'Naam is verplicht');
    });
  });
}
