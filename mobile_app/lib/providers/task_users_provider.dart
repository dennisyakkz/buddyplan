import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/preferences.dart';
import '../models/person.dart';

class TaskUser {
  final int id;
  final String name;
  final Color color;
  final bool canManageTasks;

  const TaskUser({
    required this.id,
    required this.name,
    required this.color,
    this.canManageTasks = false,
  });
}

class TaskUsersState {
  final List<TaskUser> users;
  final bool isLoading;
  final String? error;

  const TaskUsersState({
    this.users = const [],
    this.isLoading = false,
    this.error,
  });
}

class TaskUsersNotifier extends Notifier<TaskUsersState> {
  @override
  TaskUsersState build() => const TaskUsersState();

  Future<void> load() async {
    state = const TaskUsersState(isLoading: true);
    try {
      final raw = await ApiClient.instance.fetchAppUsers();
      final indexed = raw
          .asMap()
          .entries
          .map((e) => MapEntry(
              (e.value as Map<String, dynamic>)['id'] as int, e.key))
          .toList();
      await AppPreferences.ensureDefaultTaskColors(indexed);
      final colors = AppPreferences.taskPersonColors;
      final users = raw.asMap().entries.map((e) {
        final json = e.value as Map<String, dynamic>;
        final id = json['id'] as int;
        final hex = colors[id] ?? AppPreferences.colorForTaskPerson(id, e.key);
        return TaskUser(
          id: id,
          name: json['name'] as String,
          color: Person.fromJson({'id': id, 'name': json['name'], 'color': hex})
              .color,
          canManageTasks: (json['can_manage_tasks'] as bool?) ?? false,
        );
      }).toList();
      state = TaskUsersState(users: users);
    } catch (e) {
      state = TaskUsersState(error: e.toString());
    }
  }

  bool isEnabled(int personId) => AppPreferences.isTaskPersonEnabled(personId);

  Future<void> setEnabled(int personId, bool value) async {
    final map = Map<int, bool>.from(AppPreferences.taskPersonEnabled);
    map[personId] = value;
    await AppPreferences.setTaskPersonEnabled(map);
    state = TaskUsersState(users: state.users);
  }

  Future<void> setColor(int personId, String hex) async {
    final map = Map<int, String>.from(AppPreferences.taskPersonColors);
    map[personId] = hex;
    await AppPreferences.setTaskPersonColors(map);
    final h = hex.replaceFirst('#', '');
    final c = Color(int.parse('FF$h', radix: 16));
    final updated = state.users
        .map((u) => u.id == personId
            ? TaskUser(
                id: u.id,
                name: u.name,
                color: c,
                canManageTasks: u.canManageTasks,
              )
            : u)
        .toList();
    state = TaskUsersState(users: updated);
  }
}

final taskUsersProvider =
    NotifierProvider<TaskUsersNotifier, TaskUsersState>(TaskUsersNotifier.new);
