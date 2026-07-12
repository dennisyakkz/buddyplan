import '../models/calendar_event.dart';
import '../models/task_item.dart';
import '../data/dashboard_repository.dart';

/// Backward-compatible facade over [DashboardRepository].
class DataCache {
  static Future<DashboardRepository> _repo() => DashboardRepository.instance();

  static Future<List<CalendarEvent>> loadCalendarEvents() async {
    final repo = await _repo();
    final far = DateTime(2000);
    final end = DateTime(2100);
    return repo.calendarEventsForRange(far, end);
  }

  static Future<List<TaskItem>> loadTasks() async {
    final repo = await _repo();
    final far = DateTime(2000);
    final end = DateTime(2100);
    return repo.tasksForRange(far, end);
  }

  static Future<List<CalendarEvent>> calendarEventsForRange(
    DateTime start,
    DateTime end,
  ) async {
    return (await _repo()).calendarEventsForRange(start, end);
  }

  static Future<List<TaskItem>> tasksForRange(DateTime start, DateTime end) async {
    return (await _repo()).tasksForRange(start, end);
  }

  static Future<void> mergeCalendarEvents(
    List<CalendarEvent> fresh,
    DateTime start,
    DateTime end,
  ) async {
    await (await _repo()).mergeCalendarEvents(fresh, start, end);
  }

  static Future<void> mergeTasks(
    List<TaskItem> fresh,
    DateTime start,
    DateTime end,
  ) async {
    await (await _repo()).mergeTasks(fresh, start, end);
  }

  static Future<void> clear() async {
    await DashboardRepository.reset();
  }
}
