import 'dart:convert';

import 'package:drift/drift.dart';

import '../core/api_client.dart';
import '../core/network_utils.dart';
import '../core/preferences.dart';
import '../models/calendar_event.dart';
import '../models/task_item.dart';
import 'local_database.dart';

class DashboardRepository {
  DashboardRepository._();
  static DashboardRepository? _instance;
  static LocalDatabase? _db;
  static bool _migrated = false;

  static Future<DashboardRepository> instance() async {
    if (_instance == null) {
      _db = await LocalDatabase.open();
      _instance = DashboardRepository._();
      await _instance!._migrateFromSharedPreferences();
    }
    return _instance!;
  }

  static Future<void> reset() async {
    final db = _db ?? await LocalDatabase.open();
    await db.clearAll();
    _migrated = false;
  }

  static void close() {
    LocalDatabase.closeInstance();
    _instance = null;
    _db = null;
    _migrated = false;
  }

  DateTime _day(DateTime d) => DateTime(d.year, d.month, d.day);

  String _taskKey(TaskItem t) =>
      '${t.id}|${t.date.toIso8601String().split('T').first}';

  String _eventKey(CalendarEvent e) =>
      '${e.id}|${e.date.toIso8601String().split('T').first}';

  Future<void> _migrateFromSharedPreferences() async {
    if (_migrated) return;
    _migrated = true;

    final tasksJson = AppPreferences.tasksCacheJson;
    if (tasksJson != null) {
      try {
        final list = jsonDecode(tasksJson) as List<dynamic>;
        for (final raw in list) {
          final task = TaskItem.fromJson(raw as Map<String, dynamic>);
          await _upsertTask(task);
        }
      } catch (_) {}
    }

    final calendarJson = AppPreferences.calendarCacheJson;
    if (calendarJson != null) {
      try {
        final list = jsonDecode(calendarJson) as List<dynamic>;
        for (final raw in list) {
          final event =
              CalendarEvent.fromJson(raw as Map<String, dynamic>);
          await _upsertEvent(event);
        }
      } catch (_) {}
    }

    if (tasksJson != null || calendarJson != null) {
      await AppPreferences.clearDataCache();
    }
  }

  Future<List<TaskItem>> tasksForRange(DateTime start, DateTime end) async {
    final s = _day(start);
    final e = _day(end);
    final rows = await _db!.select(_db!.cachedTasks).get();
    return rows
        .map(_taskFromRow)
        .where((t) {
          final d = _day(t.date);
          return !d.isBefore(s) && !d.isAfter(e);
        })
        .toList();
  }

  Future<List<CalendarEvent>> calendarEventsForRange(
    DateTime start,
    DateTime end,
  ) async {
    final s = _day(start);
    final e = _day(end);
    final rows = await _db!.select(_db!.cachedCalendarEvents).get();
    return rows
        .map(_eventFromRow)
        .where((ev) {
          final d = _day(ev.date);
          return !d.isBefore(s) && !d.isAfter(e);
        })
        .toList();
  }

  Future<void> mergeTasks(
    List<TaskItem> fresh,
    DateTime start,
    DateTime end,
  ) async {
    final s = _day(start);
    final e = _day(end);
    final existing = await _db!.select(_db!.cachedTasks).get();
    final retained = existing.where((row) {
      final d = DateTime.parse(row.dateIso);
      final day = _day(d);
      return day.isBefore(s) || day.isAfter(e);
    });
    await _db!.batch((batch) {
      batch.deleteWhere(
        _db!.cachedTasks,
        (t) => t.dateIso.isBiggerOrEqualValue(_iso(s)) &
            t.dateIso.isSmallerOrEqualValue(_iso(e)),
      );
      for (final row in retained) {
        batch.insert(_db!.cachedTasks, row, mode: InsertMode.insertOrReplace);
      }
      for (final task in fresh) {
        batch.insert(
          _db!.cachedTasks,
          _taskToCompanion(task),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
  }

  Future<void> mergeCalendarEvents(
    List<CalendarEvent> fresh,
    DateTime start,
    DateTime end,
  ) async {
    final s = _day(start);
    final e = _day(end);
    final existing = await _db!.select(_db!.cachedCalendarEvents).get();
    final retained = existing.where((row) {
      final d = DateTime.parse(row.dateIso);
      final day = _day(d);
      return day.isBefore(s) || day.isAfter(e);
    });
    await _db!.batch((batch) {
      batch.deleteWhere(
        _db!.cachedCalendarEvents,
        (ev) => ev.dateIso.isBiggerOrEqualValue(_iso(s)) &
            ev.dateIso.isSmallerOrEqualValue(_iso(e)),
      );
      for (final row in retained) {
        batch.insert(
          _db!.cachedCalendarEvents,
          row,
          mode: InsertMode.insertOrReplace,
        );
      }
      for (final event in fresh) {
        batch.insert(
          _db!.cachedCalendarEvents,
          _eventToCompanion(event),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
  }

  Future<void> completeTaskLocal(String taskId, DateTime date) async {
    final dateIso = _iso(date);
    final cacheKey = '$taskId|$dateIso';
    final row = await (_db!.select(_db!.cachedTasks)
          ..where((t) => t.cacheKey.equals(cacheKey)))
        .getSingleOrNull();
    if (row != null) {
      await (_db!.update(_db!.cachedTasks)
            ..where((t) => t.cacheKey.equals(cacheKey)))
          .write(CachedTasksCompanion(completed: const Value(true)));
    }
    await _db!.enqueueMutation('complete_task', {
      'task_id': taskId,
      'date': dateIso,
    });
  }

  Future<TaskItem> createTaskLocal({
    required int personId,
    required Map<String, dynamic> apiPayload,
    required TaskItem optimistic,
  }) async {
    await _upsertTask(optimistic);
    await _db!.enqueueMutation('create_task', {
      'person_id': personId,
      'data': apiPayload,
      'local_id': optimistic.id,
      'date': _iso(optimistic.date),
    });
    return optimistic;
  }

  Future<CalendarEvent> createEventLocal({
    required Map<String, dynamic> apiPayload,
    required CalendarEvent optimistic,
  }) async {
    await _upsertEvent(optimistic);
    await _db!.enqueueMutation('create_event', {
      'data': apiPayload,
      'local_id': optimistic.id,
      'date': _iso(optimistic.date),
    });
    return optimistic;
  }

  Future<int> processOutbox() async {
    final pending = await _db!.pendingFifo();
    var synced = 0;
    for (final mutation in pending) {
      try {
        final payload = jsonDecode(mutation.payload) as Map<String, dynamic>;
        switch (mutation.type) {
          case 'complete_task':
            await ApiClient.instance.completeTask(
              payload['task_id'] as String,
              payload['date'] as String,
            );
            break;
          case 'create_task':
            final result = await ApiClient.instance.createTask(
              payload['person_id'] as int,
              Map<String, dynamic>.from(payload['data'] as Map),
            );
            final localId = payload['local_id'] as String;
            final dateIso = payload['date'] as String;
            final oldKey = '$localId|$dateIso';
            final newId = result['id'].toString();
            final newKey = '$newId|$dateIso';
            await (_db!.delete(_db!.cachedTasks)
                  ..where((t) => t.cacheKey.equals(oldKey)))
                .go();
            final existing = await (_db!.select(_db!.cachedTasks)
                  ..where((t) => t.cacheKey.equals(oldKey)))
                .getSingleOrNull();
            if (existing != null) {
              await _db!.into(_db!.cachedTasks).insert(
                    CachedTasksCompanion(
                      cacheKey: Value(newKey),
                      id: Value(newId),
                      title: Value(existing.title),
                      description: Value(existing.description),
                      icon: Value(existing.icon),
                      personId: Value(existing.personId),
                      dateIso: Value(existing.dateIso),
                      completed: Value(existing.completed),
                    ),
                    mode: InsertMode.insertOrReplace,
                  );
            }
            break;
          case 'create_event':
            final result = await ApiClient.instance.createCalendarEvent(
              Map<String, dynamic>.from(payload['data'] as Map),
            );
            final localId = payload['local_id'] as int;
            final dateIso = payload['date'] as String;
            final oldKey = '$localId|$dateIso';
            final newId = result['id'] as int;
            final newKey = '$newId|$dateIso';
            await (_db!.delete(_db!.cachedCalendarEvents)
                  ..where((e) => e.cacheKey.equals(oldKey)))
                .go();
            final existing = await (_db!.select(_db!.cachedCalendarEvents)
                  ..where((e) => e.cacheKey.equals(oldKey)))
                .getSingleOrNull();
            if (existing != null) {
              await _db!.into(_db!.cachedCalendarEvents).insert(
                    CachedCalendarEventsCompanion(
                      cacheKey: Value(newKey),
                      id: Value(newId),
                      title: Value(existing.title),
                      personId: Value(existing.personId),
                      dateIso: Value(existing.dateIso),
                      startTime: Value(existing.startTime),
                      endTime: Value(existing.endTime),
                    ),
                    mode: InsertMode.insertOrReplace,
                  );
            }
            break;
        }
        await (_db!.delete(_db!.pendingMutations)
              ..where((m) => m.id.equals(mutation.id)))
            .go();
        synced++;
      } catch (e) {
        if (isNetworkError(e)) break;
        await (_db!.update(_db!.pendingMutations)
              ..where((m) => m.id.equals(mutation.id)))
            .write(
          PendingMutationsCompanion(
            retryCount: Value(mutation.retryCount + 1),
            status: const Value('failed'),
          ),
        );
      }
    }
    return synced;
  }

  Future<void> _upsertTask(TaskItem task) async {
    await _db!.into(_db!.cachedTasks).insert(
          _taskToCompanion(task),
          mode: InsertMode.insertOrReplace,
        );
  }

  Future<void> _upsertEvent(CalendarEvent event) async {
    await _db!.into(_db!.cachedCalendarEvents).insert(
          _eventToCompanion(event),
          mode: InsertMode.insertOrReplace,
        );
  }

  CachedTasksCompanion _taskToCompanion(TaskItem task) {
    return CachedTasksCompanion(
      cacheKey: Value(_taskKey(task)),
      id: Value(task.id),
      title: Value(task.title),
      description: Value(task.description),
      icon: Value(task.icon),
      personId: Value(task.personId),
      dateIso: Value(_iso(task.date)),
      completed: Value(task.completed),
    );
  }

  CachedCalendarEventsCompanion _eventToCompanion(CalendarEvent event) {
    return CachedCalendarEventsCompanion(
      cacheKey: Value(_eventKey(event)),
      id: Value(event.id),
      title: Value(event.title),
      personId: Value(event.personId),
      dateIso: Value(_iso(event.date)),
      startTime: Value(event.startTime),
      endTime: Value(event.endTime),
    );
  }

  TaskItem _taskFromRow(CachedTask row) => TaskItem(
        id: row.id,
        title: row.title,
        description: row.description,
        icon: row.icon,
        personId: row.personId,
        date: DateTime.parse(row.dateIso),
        completed: row.completed,
      );

  CalendarEvent _eventFromRow(CachedCalendarEvent row) => CalendarEvent(
        id: row.id,
        title: row.title,
        personId: row.personId,
        date: DateTime.parse(row.dateIso),
        startTime: row.startTime,
        endTime: row.endTime,
      );

  String _iso(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}
