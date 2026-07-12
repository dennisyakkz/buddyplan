import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

import 'tables.dart';

part 'local_database.g.dart';

@DriftDatabase(tables: [CachedTasks, CachedCalendarEvents, PendingMutations])
class LocalDatabase extends _$LocalDatabase {
  LocalDatabase._(super.e);

  static LocalDatabase? _instance;

  static Future<LocalDatabase> open() async {
    if (_instance != null) return _instance!;
    final executor = driftDatabase(name: 'buddyplan_local.db');
    _instance = LocalDatabase._(executor);
    return _instance!;
  }

  static void closeInstance() {
    _instance?.close();
    _instance = null;
  }

  @override
  int get schemaVersion => 1;

  Future<void> clearAll() async {
    await delete(cachedTasks).go();
    await delete(cachedCalendarEvents).go();
    await delete(pendingMutations).go();
  }

  Future<List<PendingMutation>> pendingFifo() {
    return (select(pendingMutations)
          ..where((m) => m.status.equals('pending'))
          ..orderBy([(m) => OrderingTerm.asc(m.createdAt)]))
        .get();
  }

  Future<void> enqueueMutation(String type, Map<String, dynamic> payload) {
    return into(pendingMutations).insert(
      PendingMutationsCompanion.insert(
        type: type,
        payload: jsonEncode(payload),
      ),
    );
  }
}
