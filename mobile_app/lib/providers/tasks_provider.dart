import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/data_cache.dart';
import '../core/network_utils.dart';
import '../data/dashboard_repository.dart';
import '../data/sync_worker.dart';
import '../models/task_item.dart';
import '../providers/auth_provider.dart';

class TasksState {
  final List<TaskItem> tasks;
  final bool isLoading;
  final String? error;
  final bool isOffline;
  final bool hasPendingMutations;

  const TasksState({
    this.tasks = const [],
    this.isLoading = false,
    this.error,
    this.isOffline = false,
    this.hasPendingMutations = false,
  });

  List<TaskItem> tasksForDay(DateTime day) => tasks.where((t) {
        return t.date.year == day.year &&
            t.date.month == day.month &&
            t.date.day == day.day;
      }).toList();
}

class TasksNotifier extends Notifier<TasksState> {
  @override
  TasksState build() => const TasksState();

  Future<DashboardRepository> _repo() => DashboardRepository.instance();

  Future<void> loadRange(DateTime start, DateTime end,
      {bool showLoading = true}) async {
    if (showLoading) {
      if (state.tasks.isEmpty) {
        final cached = await DataCache.tasksForRange(start, end);
        state = TasksState(
          tasks: cached,
          isLoading: true,
          isOffline: cached.isNotEmpty,
        );
      } else {
        state = TasksState(
          tasks: state.tasks,
          isLoading: true,
          isOffline: state.isOffline,
        );
      }
    }
    try {
      ref.read(syncWorkerProvider)?.trigger();
      final raw = await ApiClient.instance.fetchTasks(_fmt(start), _fmt(end));
      final tasks =
          raw.map((e) => TaskItem.fromJson(e as Map<String, dynamic>)).toList();
      await DataCache.mergeTasks(tasks, start, end);
      state = TasksState(tasks: tasks);
    } catch (err) {
      if (isAuthError(err)) {
        ref.read(authProvider.notifier).handleSessionExpired();
        return;
      }
      if (isNetworkError(err)) {
        var cached = state.tasks;
        if (cached.isEmpty) {
          cached = await DataCache.tasksForRange(start, end);
        }
        if (cached.isNotEmpty) {
          state = TasksState(tasks: cached, isOffline: true);
          return;
        }
      }
      if (showLoading || state.tasks.isEmpty) {
        state = TasksState(
          error: err.toString(),
          isOffline: isNetworkError(err),
        );
      } else {
        state = TasksState(
          tasks: state.tasks,
          isOffline: isNetworkError(err),
        );
      }
    }
  }

  Future<void> completeTask(String taskId, DateTime date) async {
    final repo = await _repo();
    final updated = state.tasks.map((t) {
      if (t.id == taskId && _sameDay(t.date, date)) {
        return TaskItem(
            id: t.id,
            title: t.title,
            description: t.description,
            icon: t.icon,
            personId: t.personId,
            date: t.date,
            completed: true);
      }
      return t;
    }).toList();
    state = TasksState(
      tasks: updated,
      isOffline: true,
      hasPendingMutations: true,
    );
    await repo.completeTaskLocal(taskId, date);
    ref.read(syncWorkerProvider)?.trigger();
    try {
      await repo.processOutbox();
      state = TasksState(tasks: updated, isOffline: state.isOffline);
    } catch (_) {
      // Outbox will retry when connectivity returns.
    }
  }

  Future<void> addTaskWithPayload({
    required int personId,
    required Map<String, dynamic> apiPayload,
    required TaskItem optimistic,
  }) async {
    final repo = await _repo();
    await repo.createTaskLocal(
      personId: personId,
      apiPayload: apiPayload,
      optimistic: optimistic,
    );
    state = TasksState(
      tasks: [...state.tasks, optimistic],
      isOffline: true,
      hasPendingMutations: true,
    );
    ref.read(syncWorkerProvider)?.trigger();
    try {
      await repo.processOutbox();
      final refreshed = await DataCache.tasksForRange(
        optimistic.date,
        optimistic.date,
      );
      if (refreshed.isNotEmpty) {
        state = TasksState(tasks: [...state.tasks.where((t) => t.id != optimistic.id), ...refreshed]);
      }
    } catch (_) {}
  }

  void addTask(TaskItem task) {
    state = TasksState(
      tasks: [...state.tasks, task],
      isOffline: state.isOffline,
    );
  }

  bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  void removeTask(String id) {
    state = TasksState(
      tasks: state.tasks.where((t) => t.id != id).toList(),
      isOffline: state.isOffline,
    );
  }

  String _fmt(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

final tasksProvider =
    NotifierProvider<TasksNotifier, TasksState>(TasksNotifier.new);
