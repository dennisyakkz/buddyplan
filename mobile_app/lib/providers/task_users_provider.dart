import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/preferences.dart';

class TaskUser {
  final int id;
  final String name;
  final String profileColor;
  final bool canManageTasks;

  const TaskUser({
    required this.id,
    required this.name,
    required this.profileColor,
    this.canManageTasks = false,
  });

  factory TaskUser.fromJson(Map<String, dynamic> json) {
    return TaskUser(
      id: json['id'] as int,
      name: json['name'] as String,
      profileColor: (json['profile_color'] as String?) ?? 'teal',
      canManageTasks: (json['can_manage_tasks'] as bool?) ?? false,
    );
  }
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
      final users = raw
          .map((e) => TaskUser.fromJson(e as Map<String, dynamic>))
          .toList();
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
}

final taskUsersProvider =
    NotifierProvider<TaskUsersNotifier, TaskUsersState>(TaskUsersNotifier.new);
