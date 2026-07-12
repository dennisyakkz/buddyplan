import 'package:drift/drift.dart';

class CachedTasks extends Table {
  TextColumn get cacheKey => text()();
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get description => text().withDefault(const Constant(''))();
  TextColumn get icon => text().withDefault(const Constant('check'))();
  IntColumn get personId => integer().nullable()();
  TextColumn get dateIso => text()();
  BoolColumn get completed => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {cacheKey};
}

class CachedCalendarEvents extends Table {
  TextColumn get cacheKey => text()();
  IntColumn get id => integer()();
  TextColumn get title => text()();
  IntColumn get personId => integer()();
  TextColumn get dateIso => text()();
  TextColumn get startTime => text().nullable()();
  TextColumn get endTime => text().nullable()();

  @override
  Set<Column> get primaryKey => {cacheKey};
}

class PendingMutations extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get type => text()();
  TextColumn get payload => text()();
  DateTimeColumn get createdAt =>
      dateTime().withDefault(currentDateAndTime)();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  TextColumn get status =>
      text().withDefault(const Constant('pending'))();
}
