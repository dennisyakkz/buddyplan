// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'local_database.dart';

// ignore_for_file: type=lint
class $CachedTasksTable extends CachedTasks
    with TableInfo<$CachedTasksTable, CachedTask> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedTasksTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _cacheKeyMeta =
      const VerificationMeta('cacheKey');
  @override
  late final GeneratedColumn<String> cacheKey = GeneratedColumn<String>(
      'cache_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
      'id', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _descriptionMeta =
      const VerificationMeta('description');
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
      'description', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant(''));
  static const VerificationMeta _iconMeta = const VerificationMeta('icon');
  @override
  late final GeneratedColumn<String> icon = GeneratedColumn<String>(
      'icon', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('check'));
  static const VerificationMeta _personIdMeta =
      const VerificationMeta('personId');
  @override
  late final GeneratedColumn<int> personId = GeneratedColumn<int>(
      'person_id', aliasedName, true,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _dateIsoMeta =
      const VerificationMeta('dateIso');
  @override
  late final GeneratedColumn<String> dateIso = GeneratedColumn<String>(
      'date_iso', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _completedMeta =
      const VerificationMeta('completed');
  @override
  late final GeneratedColumn<bool> completed = GeneratedColumn<bool>(
      'completed', aliasedName, false,
      type: DriftSqlType.bool,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('CHECK ("completed" IN (0, 1))'),
      defaultValue: const Constant(false));
  @override
  List<GeneratedColumn> get $columns =>
      [cacheKey, id, title, description, icon, personId, dateIso, completed];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_tasks';
  @override
  VerificationContext validateIntegrity(Insertable<CachedTask> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('cache_key')) {
      context.handle(_cacheKeyMeta,
          cacheKey.isAcceptableOrUnknown(data['cache_key']!, _cacheKeyMeta));
    } else if (isInserting) {
      context.missing(_cacheKeyMeta);
    }
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
          _descriptionMeta,
          description.isAcceptableOrUnknown(
              data['description']!, _descriptionMeta));
    }
    if (data.containsKey('icon')) {
      context.handle(
          _iconMeta, icon.isAcceptableOrUnknown(data['icon']!, _iconMeta));
    }
    if (data.containsKey('person_id')) {
      context.handle(_personIdMeta,
          personId.isAcceptableOrUnknown(data['person_id']!, _personIdMeta));
    }
    if (data.containsKey('date_iso')) {
      context.handle(_dateIsoMeta,
          dateIso.isAcceptableOrUnknown(data['date_iso']!, _dateIsoMeta));
    } else if (isInserting) {
      context.missing(_dateIsoMeta);
    }
    if (data.containsKey('completed')) {
      context.handle(_completedMeta,
          completed.isAcceptableOrUnknown(data['completed']!, _completedMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {cacheKey};
  @override
  CachedTask map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedTask(
      cacheKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}cache_key'])!,
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}id'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      description: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}description'])!,
      icon: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}icon'])!,
      personId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}person_id']),
      dateIso: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}date_iso'])!,
      completed: attachedDatabase.typeMapping
          .read(DriftSqlType.bool, data['${effectivePrefix}completed'])!,
    );
  }

  @override
  $CachedTasksTable createAlias(String alias) {
    return $CachedTasksTable(attachedDatabase, alias);
  }
}

class CachedTask extends DataClass implements Insertable<CachedTask> {
  final String cacheKey;
  final String id;
  final String title;
  final String description;
  final String icon;
  final int? personId;
  final String dateIso;
  final bool completed;
  const CachedTask(
      {required this.cacheKey,
      required this.id,
      required this.title,
      required this.description,
      required this.icon,
      this.personId,
      required this.dateIso,
      required this.completed});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['cache_key'] = Variable<String>(cacheKey);
    map['id'] = Variable<String>(id);
    map['title'] = Variable<String>(title);
    map['description'] = Variable<String>(description);
    map['icon'] = Variable<String>(icon);
    if (!nullToAbsent || personId != null) {
      map['person_id'] = Variable<int>(personId);
    }
    map['date_iso'] = Variable<String>(dateIso);
    map['completed'] = Variable<bool>(completed);
    return map;
  }

  CachedTasksCompanion toCompanion(bool nullToAbsent) {
    return CachedTasksCompanion(
      cacheKey: Value(cacheKey),
      id: Value(id),
      title: Value(title),
      description: Value(description),
      icon: Value(icon),
      personId: personId == null && nullToAbsent
          ? const Value.absent()
          : Value(personId),
      dateIso: Value(dateIso),
      completed: Value(completed),
    );
  }

  factory CachedTask.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedTask(
      cacheKey: serializer.fromJson<String>(json['cacheKey']),
      id: serializer.fromJson<String>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      description: serializer.fromJson<String>(json['description']),
      icon: serializer.fromJson<String>(json['icon']),
      personId: serializer.fromJson<int?>(json['personId']),
      dateIso: serializer.fromJson<String>(json['dateIso']),
      completed: serializer.fromJson<bool>(json['completed']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'cacheKey': serializer.toJson<String>(cacheKey),
      'id': serializer.toJson<String>(id),
      'title': serializer.toJson<String>(title),
      'description': serializer.toJson<String>(description),
      'icon': serializer.toJson<String>(icon),
      'personId': serializer.toJson<int?>(personId),
      'dateIso': serializer.toJson<String>(dateIso),
      'completed': serializer.toJson<bool>(completed),
    };
  }

  CachedTask copyWith(
          {String? cacheKey,
          String? id,
          String? title,
          String? description,
          String? icon,
          Value<int?> personId = const Value.absent(),
          String? dateIso,
          bool? completed}) =>
      CachedTask(
        cacheKey: cacheKey ?? this.cacheKey,
        id: id ?? this.id,
        title: title ?? this.title,
        description: description ?? this.description,
        icon: icon ?? this.icon,
        personId: personId.present ? personId.value : this.personId,
        dateIso: dateIso ?? this.dateIso,
        completed: completed ?? this.completed,
      );
  CachedTask copyWithCompanion(CachedTasksCompanion data) {
    return CachedTask(
      cacheKey: data.cacheKey.present ? data.cacheKey.value : this.cacheKey,
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      description:
          data.description.present ? data.description.value : this.description,
      icon: data.icon.present ? data.icon.value : this.icon,
      personId: data.personId.present ? data.personId.value : this.personId,
      dateIso: data.dateIso.present ? data.dateIso.value : this.dateIso,
      completed: data.completed.present ? data.completed.value : this.completed,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedTask(')
          ..write('cacheKey: $cacheKey, ')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('icon: $icon, ')
          ..write('personId: $personId, ')
          ..write('dateIso: $dateIso, ')
          ..write('completed: $completed')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
      cacheKey, id, title, description, icon, personId, dateIso, completed);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedTask &&
          other.cacheKey == this.cacheKey &&
          other.id == this.id &&
          other.title == this.title &&
          other.description == this.description &&
          other.icon == this.icon &&
          other.personId == this.personId &&
          other.dateIso == this.dateIso &&
          other.completed == this.completed);
}

class CachedTasksCompanion extends UpdateCompanion<CachedTask> {
  final Value<String> cacheKey;
  final Value<String> id;
  final Value<String> title;
  final Value<String> description;
  final Value<String> icon;
  final Value<int?> personId;
  final Value<String> dateIso;
  final Value<bool> completed;
  final Value<int> rowid;
  const CachedTasksCompanion({
    this.cacheKey = const Value.absent(),
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.description = const Value.absent(),
    this.icon = const Value.absent(),
    this.personId = const Value.absent(),
    this.dateIso = const Value.absent(),
    this.completed = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedTasksCompanion.insert({
    required String cacheKey,
    required String id,
    required String title,
    this.description = const Value.absent(),
    this.icon = const Value.absent(),
    this.personId = const Value.absent(),
    required String dateIso,
    this.completed = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : cacheKey = Value(cacheKey),
        id = Value(id),
        title = Value(title),
        dateIso = Value(dateIso);
  static Insertable<CachedTask> custom({
    Expression<String>? cacheKey,
    Expression<String>? id,
    Expression<String>? title,
    Expression<String>? description,
    Expression<String>? icon,
    Expression<int>? personId,
    Expression<String>? dateIso,
    Expression<bool>? completed,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (cacheKey != null) 'cache_key': cacheKey,
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (description != null) 'description': description,
      if (icon != null) 'icon': icon,
      if (personId != null) 'person_id': personId,
      if (dateIso != null) 'date_iso': dateIso,
      if (completed != null) 'completed': completed,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedTasksCompanion copyWith(
      {Value<String>? cacheKey,
      Value<String>? id,
      Value<String>? title,
      Value<String>? description,
      Value<String>? icon,
      Value<int?>? personId,
      Value<String>? dateIso,
      Value<bool>? completed,
      Value<int>? rowid}) {
    return CachedTasksCompanion(
      cacheKey: cacheKey ?? this.cacheKey,
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      icon: icon ?? this.icon,
      personId: personId ?? this.personId,
      dateIso: dateIso ?? this.dateIso,
      completed: completed ?? this.completed,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (cacheKey.present) {
      map['cache_key'] = Variable<String>(cacheKey.value);
    }
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (icon.present) {
      map['icon'] = Variable<String>(icon.value);
    }
    if (personId.present) {
      map['person_id'] = Variable<int>(personId.value);
    }
    if (dateIso.present) {
      map['date_iso'] = Variable<String>(dateIso.value);
    }
    if (completed.present) {
      map['completed'] = Variable<bool>(completed.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedTasksCompanion(')
          ..write('cacheKey: $cacheKey, ')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('description: $description, ')
          ..write('icon: $icon, ')
          ..write('personId: $personId, ')
          ..write('dateIso: $dateIso, ')
          ..write('completed: $completed, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedCalendarEventsTable extends CachedCalendarEvents
    with TableInfo<$CachedCalendarEventsTable, CachedCalendarEvent> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedCalendarEventsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _cacheKeyMeta =
      const VerificationMeta('cacheKey');
  @override
  late final GeneratedColumn<String> cacheKey = GeneratedColumn<String>(
      'cache_key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _personIdMeta =
      const VerificationMeta('personId');
  @override
  late final GeneratedColumn<int> personId = GeneratedColumn<int>(
      'person_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _dateIsoMeta =
      const VerificationMeta('dateIso');
  @override
  late final GeneratedColumn<String> dateIso = GeneratedColumn<String>(
      'date_iso', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _startTimeMeta =
      const VerificationMeta('startTime');
  @override
  late final GeneratedColumn<String> startTime = GeneratedColumn<String>(
      'start_time', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _endTimeMeta =
      const VerificationMeta('endTime');
  @override
  late final GeneratedColumn<String> endTime = GeneratedColumn<String>(
      'end_time', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [cacheKey, id, title, personId, dateIso, startTime, endTime];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_calendar_events';
  @override
  VerificationContext validateIntegrity(
      Insertable<CachedCalendarEvent> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('cache_key')) {
      context.handle(_cacheKeyMeta,
          cacheKey.isAcceptableOrUnknown(data['cache_key']!, _cacheKeyMeta));
    } else if (isInserting) {
      context.missing(_cacheKeyMeta);
    }
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('person_id')) {
      context.handle(_personIdMeta,
          personId.isAcceptableOrUnknown(data['person_id']!, _personIdMeta));
    } else if (isInserting) {
      context.missing(_personIdMeta);
    }
    if (data.containsKey('date_iso')) {
      context.handle(_dateIsoMeta,
          dateIso.isAcceptableOrUnknown(data['date_iso']!, _dateIsoMeta));
    } else if (isInserting) {
      context.missing(_dateIsoMeta);
    }
    if (data.containsKey('start_time')) {
      context.handle(_startTimeMeta,
          startTime.isAcceptableOrUnknown(data['start_time']!, _startTimeMeta));
    }
    if (data.containsKey('end_time')) {
      context.handle(_endTimeMeta,
          endTime.isAcceptableOrUnknown(data['end_time']!, _endTimeMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {cacheKey};
  @override
  CachedCalendarEvent map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedCalendarEvent(
      cacheKey: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}cache_key'])!,
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      personId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}person_id'])!,
      dateIso: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}date_iso'])!,
      startTime: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}start_time']),
      endTime: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}end_time']),
    );
  }

  @override
  $CachedCalendarEventsTable createAlias(String alias) {
    return $CachedCalendarEventsTable(attachedDatabase, alias);
  }
}

class CachedCalendarEvent extends DataClass
    implements Insertable<CachedCalendarEvent> {
  final String cacheKey;
  final int id;
  final String title;
  final int personId;
  final String dateIso;
  final String? startTime;
  final String? endTime;
  const CachedCalendarEvent(
      {required this.cacheKey,
      required this.id,
      required this.title,
      required this.personId,
      required this.dateIso,
      this.startTime,
      this.endTime});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['cache_key'] = Variable<String>(cacheKey);
    map['id'] = Variable<int>(id);
    map['title'] = Variable<String>(title);
    map['person_id'] = Variable<int>(personId);
    map['date_iso'] = Variable<String>(dateIso);
    if (!nullToAbsent || startTime != null) {
      map['start_time'] = Variable<String>(startTime);
    }
    if (!nullToAbsent || endTime != null) {
      map['end_time'] = Variable<String>(endTime);
    }
    return map;
  }

  CachedCalendarEventsCompanion toCompanion(bool nullToAbsent) {
    return CachedCalendarEventsCompanion(
      cacheKey: Value(cacheKey),
      id: Value(id),
      title: Value(title),
      personId: Value(personId),
      dateIso: Value(dateIso),
      startTime: startTime == null && nullToAbsent
          ? const Value.absent()
          : Value(startTime),
      endTime: endTime == null && nullToAbsent
          ? const Value.absent()
          : Value(endTime),
    );
  }

  factory CachedCalendarEvent.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedCalendarEvent(
      cacheKey: serializer.fromJson<String>(json['cacheKey']),
      id: serializer.fromJson<int>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      personId: serializer.fromJson<int>(json['personId']),
      dateIso: serializer.fromJson<String>(json['dateIso']),
      startTime: serializer.fromJson<String?>(json['startTime']),
      endTime: serializer.fromJson<String?>(json['endTime']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'cacheKey': serializer.toJson<String>(cacheKey),
      'id': serializer.toJson<int>(id),
      'title': serializer.toJson<String>(title),
      'personId': serializer.toJson<int>(personId),
      'dateIso': serializer.toJson<String>(dateIso),
      'startTime': serializer.toJson<String?>(startTime),
      'endTime': serializer.toJson<String?>(endTime),
    };
  }

  CachedCalendarEvent copyWith(
          {String? cacheKey,
          int? id,
          String? title,
          int? personId,
          String? dateIso,
          Value<String?> startTime = const Value.absent(),
          Value<String?> endTime = const Value.absent()}) =>
      CachedCalendarEvent(
        cacheKey: cacheKey ?? this.cacheKey,
        id: id ?? this.id,
        title: title ?? this.title,
        personId: personId ?? this.personId,
        dateIso: dateIso ?? this.dateIso,
        startTime: startTime.present ? startTime.value : this.startTime,
        endTime: endTime.present ? endTime.value : this.endTime,
      );
  CachedCalendarEvent copyWithCompanion(CachedCalendarEventsCompanion data) {
    return CachedCalendarEvent(
      cacheKey: data.cacheKey.present ? data.cacheKey.value : this.cacheKey,
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      personId: data.personId.present ? data.personId.value : this.personId,
      dateIso: data.dateIso.present ? data.dateIso.value : this.dateIso,
      startTime: data.startTime.present ? data.startTime.value : this.startTime,
      endTime: data.endTime.present ? data.endTime.value : this.endTime,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedCalendarEvent(')
          ..write('cacheKey: $cacheKey, ')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('personId: $personId, ')
          ..write('dateIso: $dateIso, ')
          ..write('startTime: $startTime, ')
          ..write('endTime: $endTime')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(cacheKey, id, title, personId, dateIso, startTime, endTime);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedCalendarEvent &&
          other.cacheKey == this.cacheKey &&
          other.id == this.id &&
          other.title == this.title &&
          other.personId == this.personId &&
          other.dateIso == this.dateIso &&
          other.startTime == this.startTime &&
          other.endTime == this.endTime);
}

class CachedCalendarEventsCompanion
    extends UpdateCompanion<CachedCalendarEvent> {
  final Value<String> cacheKey;
  final Value<int> id;
  final Value<String> title;
  final Value<int> personId;
  final Value<String> dateIso;
  final Value<String?> startTime;
  final Value<String?> endTime;
  final Value<int> rowid;
  const CachedCalendarEventsCompanion({
    this.cacheKey = const Value.absent(),
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.personId = const Value.absent(),
    this.dateIso = const Value.absent(),
    this.startTime = const Value.absent(),
    this.endTime = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedCalendarEventsCompanion.insert({
    required String cacheKey,
    required int id,
    required String title,
    required int personId,
    required String dateIso,
    this.startTime = const Value.absent(),
    this.endTime = const Value.absent(),
    this.rowid = const Value.absent(),
  })  : cacheKey = Value(cacheKey),
        id = Value(id),
        title = Value(title),
        personId = Value(personId),
        dateIso = Value(dateIso);
  static Insertable<CachedCalendarEvent> custom({
    Expression<String>? cacheKey,
    Expression<int>? id,
    Expression<String>? title,
    Expression<int>? personId,
    Expression<String>? dateIso,
    Expression<String>? startTime,
    Expression<String>? endTime,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (cacheKey != null) 'cache_key': cacheKey,
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (personId != null) 'person_id': personId,
      if (dateIso != null) 'date_iso': dateIso,
      if (startTime != null) 'start_time': startTime,
      if (endTime != null) 'end_time': endTime,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedCalendarEventsCompanion copyWith(
      {Value<String>? cacheKey,
      Value<int>? id,
      Value<String>? title,
      Value<int>? personId,
      Value<String>? dateIso,
      Value<String?>? startTime,
      Value<String?>? endTime,
      Value<int>? rowid}) {
    return CachedCalendarEventsCompanion(
      cacheKey: cacheKey ?? this.cacheKey,
      id: id ?? this.id,
      title: title ?? this.title,
      personId: personId ?? this.personId,
      dateIso: dateIso ?? this.dateIso,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (cacheKey.present) {
      map['cache_key'] = Variable<String>(cacheKey.value);
    }
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (personId.present) {
      map['person_id'] = Variable<int>(personId.value);
    }
    if (dateIso.present) {
      map['date_iso'] = Variable<String>(dateIso.value);
    }
    if (startTime.present) {
      map['start_time'] = Variable<String>(startTime.value);
    }
    if (endTime.present) {
      map['end_time'] = Variable<String>(endTime.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedCalendarEventsCompanion(')
          ..write('cacheKey: $cacheKey, ')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('personId: $personId, ')
          ..write('dateIso: $dateIso, ')
          ..write('startTime: $startTime, ')
          ..write('endTime: $endTime, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $PendingMutationsTable extends PendingMutations
    with TableInfo<$PendingMutationsTable, PendingMutation> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PendingMutationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
      'type', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _payloadMeta =
      const VerificationMeta('payload');
  @override
  late final GeneratedColumn<String> payload = GeneratedColumn<String>(
      'payload', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, false,
      type: DriftSqlType.dateTime,
      requiredDuringInsert: false,
      defaultValue: currentDateAndTime);
  static const VerificationMeta _retryCountMeta =
      const VerificationMeta('retryCount');
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
      'retry_count', aliasedName, false,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultValue: const Constant(0));
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
      'status', aliasedName, false,
      type: DriftSqlType.string,
      requiredDuringInsert: false,
      defaultValue: const Constant('pending'));
  @override
  List<GeneratedColumn> get $columns =>
      [id, type, payload, createdAt, retryCount, status];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pending_mutations';
  @override
  VerificationContext validateIntegrity(Insertable<PendingMutation> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('type')) {
      context.handle(
          _typeMeta, type.isAcceptableOrUnknown(data['type']!, _typeMeta));
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('payload')) {
      context.handle(_payloadMeta,
          payload.isAcceptableOrUnknown(data['payload']!, _payloadMeta));
    } else if (isInserting) {
      context.missing(_payloadMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    }
    if (data.containsKey('retry_count')) {
      context.handle(
          _retryCountMeta,
          retryCount.isAcceptableOrUnknown(
              data['retry_count']!, _retryCountMeta));
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PendingMutation map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PendingMutation(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      type: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}type'])!,
      payload: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}payload'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at'])!,
      retryCount: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}retry_count'])!,
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}status'])!,
    );
  }

  @override
  $PendingMutationsTable createAlias(String alias) {
    return $PendingMutationsTable(attachedDatabase, alias);
  }
}

class PendingMutation extends DataClass implements Insertable<PendingMutation> {
  final int id;
  final String type;
  final String payload;
  final DateTime createdAt;
  final int retryCount;
  final String status;
  const PendingMutation(
      {required this.id,
      required this.type,
      required this.payload,
      required this.createdAt,
      required this.retryCount,
      required this.status});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['type'] = Variable<String>(type);
    map['payload'] = Variable<String>(payload);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['retry_count'] = Variable<int>(retryCount);
    map['status'] = Variable<String>(status);
    return map;
  }

  PendingMutationsCompanion toCompanion(bool nullToAbsent) {
    return PendingMutationsCompanion(
      id: Value(id),
      type: Value(type),
      payload: Value(payload),
      createdAt: Value(createdAt),
      retryCount: Value(retryCount),
      status: Value(status),
    );
  }

  factory PendingMutation.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PendingMutation(
      id: serializer.fromJson<int>(json['id']),
      type: serializer.fromJson<String>(json['type']),
      payload: serializer.fromJson<String>(json['payload']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
      status: serializer.fromJson<String>(json['status']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'type': serializer.toJson<String>(type),
      'payload': serializer.toJson<String>(payload),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'retryCount': serializer.toJson<int>(retryCount),
      'status': serializer.toJson<String>(status),
    };
  }

  PendingMutation copyWith(
          {int? id,
          String? type,
          String? payload,
          DateTime? createdAt,
          int? retryCount,
          String? status}) =>
      PendingMutation(
        id: id ?? this.id,
        type: type ?? this.type,
        payload: payload ?? this.payload,
        createdAt: createdAt ?? this.createdAt,
        retryCount: retryCount ?? this.retryCount,
        status: status ?? this.status,
      );
  PendingMutation copyWithCompanion(PendingMutationsCompanion data) {
    return PendingMutation(
      id: data.id.present ? data.id.value : this.id,
      type: data.type.present ? data.type.value : this.type,
      payload: data.payload.present ? data.payload.value : this.payload,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      retryCount:
          data.retryCount.present ? data.retryCount.value : this.retryCount,
      status: data.status.present ? data.status.value : this.status,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PendingMutation(')
          ..write('id: $id, ')
          ..write('type: $type, ')
          ..write('payload: $payload, ')
          ..write('createdAt: $createdAt, ')
          ..write('retryCount: $retryCount, ')
          ..write('status: $status')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, type, payload, createdAt, retryCount, status);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PendingMutation &&
          other.id == this.id &&
          other.type == this.type &&
          other.payload == this.payload &&
          other.createdAt == this.createdAt &&
          other.retryCount == this.retryCount &&
          other.status == this.status);
}

class PendingMutationsCompanion extends UpdateCompanion<PendingMutation> {
  final Value<int> id;
  final Value<String> type;
  final Value<String> payload;
  final Value<DateTime> createdAt;
  final Value<int> retryCount;
  final Value<String> status;
  const PendingMutationsCompanion({
    this.id = const Value.absent(),
    this.type = const Value.absent(),
    this.payload = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.status = const Value.absent(),
  });
  PendingMutationsCompanion.insert({
    this.id = const Value.absent(),
    required String type,
    required String payload,
    this.createdAt = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.status = const Value.absent(),
  })  : type = Value(type),
        payload = Value(payload);
  static Insertable<PendingMutation> custom({
    Expression<int>? id,
    Expression<String>? type,
    Expression<String>? payload,
    Expression<DateTime>? createdAt,
    Expression<int>? retryCount,
    Expression<String>? status,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (type != null) 'type': type,
      if (payload != null) 'payload': payload,
      if (createdAt != null) 'created_at': createdAt,
      if (retryCount != null) 'retry_count': retryCount,
      if (status != null) 'status': status,
    });
  }

  PendingMutationsCompanion copyWith(
      {Value<int>? id,
      Value<String>? type,
      Value<String>? payload,
      Value<DateTime>? createdAt,
      Value<int>? retryCount,
      Value<String>? status}) {
    return PendingMutationsCompanion(
      id: id ?? this.id,
      type: type ?? this.type,
      payload: payload ?? this.payload,
      createdAt: createdAt ?? this.createdAt,
      retryCount: retryCount ?? this.retryCount,
      status: status ?? this.status,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (payload.present) {
      map['payload'] = Variable<String>(payload.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PendingMutationsCompanion(')
          ..write('id: $id, ')
          ..write('type: $type, ')
          ..write('payload: $payload, ')
          ..write('createdAt: $createdAt, ')
          ..write('retryCount: $retryCount, ')
          ..write('status: $status')
          ..write(')'))
        .toString();
  }
}

abstract class _$LocalDatabase extends GeneratedDatabase {
  _$LocalDatabase(QueryExecutor e) : super(e);
  $LocalDatabaseManager get managers => $LocalDatabaseManager(this);
  late final $CachedTasksTable cachedTasks = $CachedTasksTable(this);
  late final $CachedCalendarEventsTable cachedCalendarEvents =
      $CachedCalendarEventsTable(this);
  late final $PendingMutationsTable pendingMutations =
      $PendingMutationsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [cachedTasks, cachedCalendarEvents, pendingMutations];
}

typedef $$CachedTasksTableCreateCompanionBuilder = CachedTasksCompanion
    Function({
  required String cacheKey,
  required String id,
  required String title,
  Value<String> description,
  Value<String> icon,
  Value<int?> personId,
  required String dateIso,
  Value<bool> completed,
  Value<int> rowid,
});
typedef $$CachedTasksTableUpdateCompanionBuilder = CachedTasksCompanion
    Function({
  Value<String> cacheKey,
  Value<String> id,
  Value<String> title,
  Value<String> description,
  Value<String> icon,
  Value<int?> personId,
  Value<String> dateIso,
  Value<bool> completed,
  Value<int> rowid,
});

class $$CachedTasksTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedTasksTable> {
  $$CachedTasksTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get cacheKey => $composableBuilder(
      column: $table.cacheKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get icon => $composableBuilder(
      column: $table.icon, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get personId => $composableBuilder(
      column: $table.personId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get dateIso => $composableBuilder(
      column: $table.dateIso, builder: (column) => ColumnFilters(column));

  ColumnFilters<bool> get completed => $composableBuilder(
      column: $table.completed, builder: (column) => ColumnFilters(column));
}

class $$CachedTasksTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedTasksTable> {
  $$CachedTasksTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get cacheKey => $composableBuilder(
      column: $table.cacheKey, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get icon => $composableBuilder(
      column: $table.icon, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get personId => $composableBuilder(
      column: $table.personId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get dateIso => $composableBuilder(
      column: $table.dateIso, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<bool> get completed => $composableBuilder(
      column: $table.completed, builder: (column) => ColumnOrderings(column));
}

class $$CachedTasksTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedTasksTable> {
  $$CachedTasksTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get cacheKey =>
      $composableBuilder(column: $table.cacheKey, builder: (column) => column);

  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
      column: $table.description, builder: (column) => column);

  GeneratedColumn<String> get icon =>
      $composableBuilder(column: $table.icon, builder: (column) => column);

  GeneratedColumn<int> get personId =>
      $composableBuilder(column: $table.personId, builder: (column) => column);

  GeneratedColumn<String> get dateIso =>
      $composableBuilder(column: $table.dateIso, builder: (column) => column);

  GeneratedColumn<bool> get completed =>
      $composableBuilder(column: $table.completed, builder: (column) => column);
}

class $$CachedTasksTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedTasksTable,
    CachedTask,
    $$CachedTasksTableFilterComposer,
    $$CachedTasksTableOrderingComposer,
    $$CachedTasksTableAnnotationComposer,
    $$CachedTasksTableCreateCompanionBuilder,
    $$CachedTasksTableUpdateCompanionBuilder,
    (
      CachedTask,
      BaseReferences<_$LocalDatabase, $CachedTasksTable, CachedTask>
    ),
    CachedTask,
    PrefetchHooks Function()> {
  $$CachedTasksTableTableManager(_$LocalDatabase db, $CachedTasksTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedTasksTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedTasksTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedTasksTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> cacheKey = const Value.absent(),
            Value<String> id = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String> description = const Value.absent(),
            Value<String> icon = const Value.absent(),
            Value<int?> personId = const Value.absent(),
            Value<String> dateIso = const Value.absent(),
            Value<bool> completed = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTasksCompanion(
            cacheKey: cacheKey,
            id: id,
            title: title,
            description: description,
            icon: icon,
            personId: personId,
            dateIso: dateIso,
            completed: completed,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String cacheKey,
            required String id,
            required String title,
            Value<String> description = const Value.absent(),
            Value<String> icon = const Value.absent(),
            Value<int?> personId = const Value.absent(),
            required String dateIso,
            Value<bool> completed = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedTasksCompanion.insert(
            cacheKey: cacheKey,
            id: id,
            title: title,
            description: description,
            icon: icon,
            personId: personId,
            dateIso: dateIso,
            completed: completed,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedTasksTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $CachedTasksTable,
    CachedTask,
    $$CachedTasksTableFilterComposer,
    $$CachedTasksTableOrderingComposer,
    $$CachedTasksTableAnnotationComposer,
    $$CachedTasksTableCreateCompanionBuilder,
    $$CachedTasksTableUpdateCompanionBuilder,
    (
      CachedTask,
      BaseReferences<_$LocalDatabase, $CachedTasksTable, CachedTask>
    ),
    CachedTask,
    PrefetchHooks Function()>;
typedef $$CachedCalendarEventsTableCreateCompanionBuilder
    = CachedCalendarEventsCompanion Function({
  required String cacheKey,
  required int id,
  required String title,
  required int personId,
  required String dateIso,
  Value<String?> startTime,
  Value<String?> endTime,
  Value<int> rowid,
});
typedef $$CachedCalendarEventsTableUpdateCompanionBuilder
    = CachedCalendarEventsCompanion Function({
  Value<String> cacheKey,
  Value<int> id,
  Value<String> title,
  Value<int> personId,
  Value<String> dateIso,
  Value<String?> startTime,
  Value<String?> endTime,
  Value<int> rowid,
});

class $$CachedCalendarEventsTableFilterComposer
    extends Composer<_$LocalDatabase, $CachedCalendarEventsTable> {
  $$CachedCalendarEventsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get cacheKey => $composableBuilder(
      column: $table.cacheKey, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get personId => $composableBuilder(
      column: $table.personId, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get dateIso => $composableBuilder(
      column: $table.dateIso, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get startTime => $composableBuilder(
      column: $table.startTime, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get endTime => $composableBuilder(
      column: $table.endTime, builder: (column) => ColumnFilters(column));
}

class $$CachedCalendarEventsTableOrderingComposer
    extends Composer<_$LocalDatabase, $CachedCalendarEventsTable> {
  $$CachedCalendarEventsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get cacheKey => $composableBuilder(
      column: $table.cacheKey, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get personId => $composableBuilder(
      column: $table.personId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get dateIso => $composableBuilder(
      column: $table.dateIso, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get startTime => $composableBuilder(
      column: $table.startTime, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get endTime => $composableBuilder(
      column: $table.endTime, builder: (column) => ColumnOrderings(column));
}

class $$CachedCalendarEventsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $CachedCalendarEventsTable> {
  $$CachedCalendarEventsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get cacheKey =>
      $composableBuilder(column: $table.cacheKey, builder: (column) => column);

  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<int> get personId =>
      $composableBuilder(column: $table.personId, builder: (column) => column);

  GeneratedColumn<String> get dateIso =>
      $composableBuilder(column: $table.dateIso, builder: (column) => column);

  GeneratedColumn<String> get startTime =>
      $composableBuilder(column: $table.startTime, builder: (column) => column);

  GeneratedColumn<String> get endTime =>
      $composableBuilder(column: $table.endTime, builder: (column) => column);
}

class $$CachedCalendarEventsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $CachedCalendarEventsTable,
    CachedCalendarEvent,
    $$CachedCalendarEventsTableFilterComposer,
    $$CachedCalendarEventsTableOrderingComposer,
    $$CachedCalendarEventsTableAnnotationComposer,
    $$CachedCalendarEventsTableCreateCompanionBuilder,
    $$CachedCalendarEventsTableUpdateCompanionBuilder,
    (
      CachedCalendarEvent,
      BaseReferences<_$LocalDatabase, $CachedCalendarEventsTable,
          CachedCalendarEvent>
    ),
    CachedCalendarEvent,
    PrefetchHooks Function()> {
  $$CachedCalendarEventsTableTableManager(
      _$LocalDatabase db, $CachedCalendarEventsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedCalendarEventsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedCalendarEventsTableOrderingComposer(
                  $db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedCalendarEventsTableAnnotationComposer(
                  $db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> cacheKey = const Value.absent(),
            Value<int> id = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<int> personId = const Value.absent(),
            Value<String> dateIso = const Value.absent(),
            Value<String?> startTime = const Value.absent(),
            Value<String?> endTime = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedCalendarEventsCompanion(
            cacheKey: cacheKey,
            id: id,
            title: title,
            personId: personId,
            dateIso: dateIso,
            startTime: startTime,
            endTime: endTime,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String cacheKey,
            required int id,
            required String title,
            required int personId,
            required String dateIso,
            Value<String?> startTime = const Value.absent(),
            Value<String?> endTime = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              CachedCalendarEventsCompanion.insert(
            cacheKey: cacheKey,
            id: id,
            title: title,
            personId: personId,
            dateIso: dateIso,
            startTime: startTime,
            endTime: endTime,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$CachedCalendarEventsTableProcessedTableManager
    = ProcessedTableManager<
        _$LocalDatabase,
        $CachedCalendarEventsTable,
        CachedCalendarEvent,
        $$CachedCalendarEventsTableFilterComposer,
        $$CachedCalendarEventsTableOrderingComposer,
        $$CachedCalendarEventsTableAnnotationComposer,
        $$CachedCalendarEventsTableCreateCompanionBuilder,
        $$CachedCalendarEventsTableUpdateCompanionBuilder,
        (
          CachedCalendarEvent,
          BaseReferences<_$LocalDatabase, $CachedCalendarEventsTable,
              CachedCalendarEvent>
        ),
        CachedCalendarEvent,
        PrefetchHooks Function()>;
typedef $$PendingMutationsTableCreateCompanionBuilder
    = PendingMutationsCompanion Function({
  Value<int> id,
  required String type,
  required String payload,
  Value<DateTime> createdAt,
  Value<int> retryCount,
  Value<String> status,
});
typedef $$PendingMutationsTableUpdateCompanionBuilder
    = PendingMutationsCompanion Function({
  Value<int> id,
  Value<String> type,
  Value<String> payload,
  Value<DateTime> createdAt,
  Value<int> retryCount,
  Value<String> status,
});

class $$PendingMutationsTableFilterComposer
    extends Composer<_$LocalDatabase, $PendingMutationsTable> {
  $$PendingMutationsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get type => $composableBuilder(
      column: $table.type, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get payload => $composableBuilder(
      column: $table.payload, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));
}

class $$PendingMutationsTableOrderingComposer
    extends Composer<_$LocalDatabase, $PendingMutationsTable> {
  $$PendingMutationsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get type => $composableBuilder(
      column: $table.type, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get payload => $composableBuilder(
      column: $table.payload, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));
}

class $$PendingMutationsTableAnnotationComposer
    extends Composer<_$LocalDatabase, $PendingMutationsTable> {
  $$PendingMutationsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get type =>
      $composableBuilder(column: $table.type, builder: (column) => column);

  GeneratedColumn<String> get payload =>
      $composableBuilder(column: $table.payload, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<int> get retryCount => $composableBuilder(
      column: $table.retryCount, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);
}

class $$PendingMutationsTableTableManager extends RootTableManager<
    _$LocalDatabase,
    $PendingMutationsTable,
    PendingMutation,
    $$PendingMutationsTableFilterComposer,
    $$PendingMutationsTableOrderingComposer,
    $$PendingMutationsTableAnnotationComposer,
    $$PendingMutationsTableCreateCompanionBuilder,
    $$PendingMutationsTableUpdateCompanionBuilder,
    (
      PendingMutation,
      BaseReferences<_$LocalDatabase, $PendingMutationsTable, PendingMutation>
    ),
    PendingMutation,
    PrefetchHooks Function()> {
  $$PendingMutationsTableTableManager(
      _$LocalDatabase db, $PendingMutationsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PendingMutationsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PendingMutationsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PendingMutationsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> type = const Value.absent(),
            Value<String> payload = const Value.absent(),
            Value<DateTime> createdAt = const Value.absent(),
            Value<int> retryCount = const Value.absent(),
            Value<String> status = const Value.absent(),
          }) =>
              PendingMutationsCompanion(
            id: id,
            type: type,
            payload: payload,
            createdAt: createdAt,
            retryCount: retryCount,
            status: status,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String type,
            required String payload,
            Value<DateTime> createdAt = const Value.absent(),
            Value<int> retryCount = const Value.absent(),
            Value<String> status = const Value.absent(),
          }) =>
              PendingMutationsCompanion.insert(
            id: id,
            type: type,
            payload: payload,
            createdAt: createdAt,
            retryCount: retryCount,
            status: status,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$PendingMutationsTableProcessedTableManager = ProcessedTableManager<
    _$LocalDatabase,
    $PendingMutationsTable,
    PendingMutation,
    $$PendingMutationsTableFilterComposer,
    $$PendingMutationsTableOrderingComposer,
    $$PendingMutationsTableAnnotationComposer,
    $$PendingMutationsTableCreateCompanionBuilder,
    $$PendingMutationsTableUpdateCompanionBuilder,
    (
      PendingMutation,
      BaseReferences<_$LocalDatabase, $PendingMutationsTable, PendingMutation>
    ),
    PendingMutation,
    PrefetchHooks Function()>;

class $LocalDatabaseManager {
  final _$LocalDatabase _db;
  $LocalDatabaseManager(this._db);
  $$CachedTasksTableTableManager get cachedTasks =>
      $$CachedTasksTableTableManager(_db, _db.cachedTasks);
  $$CachedCalendarEventsTableTableManager get cachedCalendarEvents =>
      $$CachedCalendarEventsTableTableManager(_db, _db.cachedCalendarEvents);
  $$PendingMutationsTableTableManager get pendingMutations =>
      $$PendingMutationsTableTableManager(_db, _db.pendingMutations);
}
