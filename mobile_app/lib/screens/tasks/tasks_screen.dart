import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/person.dart';
import '../../models/task_item.dart';
import '../../providers/tasks_provider.dart';
import '../../providers/task_users_provider.dart';
import '../../widgets/task_user_settings_row.dart';
import '../../widgets/outlook_refresh_indicator.dart';
import '../settings/settings_screen.dart';
import 'views/day_tasks_view.dart';
import 'views/week_tasks_view.dart';
import 'add_task_sheet.dart';
import 'task_detail_screen.dart';

enum TasksView { day, week }

class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  TasksView _view = TasksView.day;
  DateTime _focusedDay = DateTime.now();
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _refreshTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) _refreshCurrentRange();
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadCurrentRange();
      ref.read(taskUsersProvider.notifier).load();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _loadCurrentRange() {
    final start = _view == TasksView.week
        ? _monday(_focusedDay)
        : _focusedDay;
    final end = _view == TasksView.week
        ? _monday(_focusedDay).add(const Duration(days: 6))
        : _focusedDay;
    ref.read(tasksProvider.notifier).loadRange(start, end);
  }

  Future<void> _refreshCurrentRange() {
    final start = _view == TasksView.week
        ? _monday(_focusedDay)
        : _focusedDay;
    final end = _view == TasksView.week
        ? _monday(_focusedDay).add(const Duration(days: 6))
        : _focusedDay;
    return ref
        .read(tasksProvider.notifier)
        .loadRange(start, end, showLoading: false);
  }

  DateTime _monday(DateTime d) =>
      d.subtract(Duration(days: d.weekday - 1));

  String get _viewLabel => _view == TasksView.day ? 'Dag' : 'Week';

  @override
  Widget build(BuildContext context) {
    final tasksState = ref.watch(tasksProvider);
    final taskUsersState = ref.watch(taskUsersProvider);
    final taskUsersNotifier = ref.read(taskUsersProvider.notifier);
    final visiblePersons = taskUsersState.users
        .where((u) => taskUsersNotifier.isEnabled(u.id))
        .map((u) => Person(
              id: u.id,
              name: u.name,
              isMe: false,
              profileColor: u.profileColor,
            ))
        .toList();
    final enabledIds = visiblePersons.map((p) => p.id).toSet();

    final manageableIds = taskUsersState.users
        .where((u) => u.canManageTasks)
        .map((u) => u.id)
        .toSet();
    final canManageAny = manageableIds.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: Text('Taken – $_viewLabel'),
        actions: [
          Builder(
            builder: (scaffoldContext) => IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => Scaffold.of(scaffoldContext).openEndDrawer(),
              tooltip: 'Menu',
            ),
          ),
        ],
      ),
      endDrawer: _buildDrawer(context),
      body: _buildBody(tasksState, visiblePersons, enabledIds, manageableIds),
      floatingActionButton: canManageAny
          ? FloatingActionButton(
              onPressed: () => _openAddTask(context),
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  Widget _buildBody(
    TasksState tasksState,
    List<Person> persons,
    Set<int> enabledIds,
    Set<int> manageableIds,
  ) {
    if (tasksState.isLoading && tasksState.tasks.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (tasksState.error != null && tasksState.tasks.isEmpty) {
      return OutlookRefreshIndicator(
        onRefresh: _refreshCurrentRange,
        child: ListView(
          physics: alwaysScrollable,
          children: [
            const SizedBox(height: 120),
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(tasksState.error!, textAlign: TextAlign.center),
            ),
            const SizedBox(height: 12),
            Center(
              child: ElevatedButton(
                  onPressed: _loadCurrentRange, child: const Text('Opnieuw')),
            ),
          ],
        ),
      );
    }

    final visibleTasks = tasksState.tasks
        .where((t) => enabledIds.contains(t.personId))
        .toList();
    final filteredState = TasksState(
      tasks: visibleTasks,
      isLoading: tasksState.isLoading,
      error: tasksState.error,
    );

    switch (_view) {
      case TasksView.day:
        return DayTasksView(
          tasks: filteredState.tasksForDay(_focusedDay),
          persons: persons,
          day: _focusedDay,
          manageableIds: manageableIds,
          onRefresh: _refreshCurrentRange,
          onPrev: () => setState(() {
            _focusedDay = _focusedDay.subtract(const Duration(days: 1));
            _loadCurrentRange();
          }),
          onNext: () => setState(() {
            _focusedDay = _focusedDay.add(const Duration(days: 1));
            _loadCurrentRange();
          }),
          onComplete: (task) {
            ref.read(tasksProvider.notifier).completeTask(task.id, task.date);
          },
          onOpen: (task) => _openTask(context, task, persons),
        );
      case TasksView.week:
        final monday = _monday(_focusedDay);
        final days =
            List.generate(7, (i) => monday.add(Duration(days: i)));
        return WeekTasksView(
          days: days,
          tasksForDay: (day) => filteredState.tasksForDay(day),
          persons: persons,
          manageableIds: manageableIds,
          onRefresh: _refreshCurrentRange,
          onPrev: () => setState(() {
            _focusedDay = _focusedDay.subtract(const Duration(days: 7));
            _loadCurrentRange();
          }),
          onNext: () => setState(() {
            _focusedDay = _focusedDay.add(const Duration(days: 7));
            _loadCurrentRange();
          }),
          onComplete: (task) {
            ref.read(tasksProvider.notifier).completeTask(task.id, task.date);
          },
          onOpen: (task) => _openTask(context, task, persons),
        );
    }
  }

  Future<void> _openTask(
    BuildContext context,
    TaskItem task,
    List<Person> persons,
  ) async {
    final canEdit = task.personId != null &&
        ref.read(taskUsersProvider).users.any(
              (u) => u.id == task.personId && u.canManageTasks,
            );
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => TaskDetailScreen(
          task: task,
          persons: persons,
          canEdit: canEdit,
        ),
      ),
    );
    if (changed == true) _loadCurrentRange();
  }

  Widget _buildDrawer(BuildContext context) {
    final taskUsersState = ref.watch(taskUsersProvider);

    return Drawer(
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Text('Weergave',
                  style: Theme.of(context).textTheme.titleSmall),
            ),
            _viewTile(
                context, TasksView.day, Icons.today, 'Dag – vandaag'),
            _viewTile(
                context, TasksView.week, Icons.view_week, 'Week'),
            const Divider(),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
              child: Text('Gebruikers',
                  style: Theme.of(context).textTheme.titleSmall),
            ),
            Expanded(
              child: taskUsersState.isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : taskUsersState.error != null
                      ? Padding(
                          padding: const EdgeInsets.all(16),
                          child: Text(taskUsersState.error!,
                              style: const TextStyle(color: Colors.red)),
                        )
                      : taskUsersState.users.isEmpty
                          ? const Padding(
                              padding: EdgeInsets.all(16),
                              child: Text(
                                  'Geen gebruikers met taken gevonden.'),
                            )
                          : ListView(
                              children: taskUsersState.users
                                  .map((user) => TaskUserSettingsRow(
                                        user: user,
                                        showDivider: true,
                                      ))
                                  .toList(),
                            ),
            ),
            const Divider(),
            ListTile(
              leading: const Icon(Icons.settings),
              title: const Text('Instellingen'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const SettingsScreen(),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  ListTile _viewTile(
      BuildContext context, TasksView v, IconData icon, String label) {
    final selected = _view == v;
    return ListTile(
      leading: Icon(icon,
          color: selected ? Theme.of(context).colorScheme.primary : null),
      title: Text(label,
          style: selected
              ? TextStyle(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.bold)
              : null),
      selected: selected,
      onTap: () {
        setState(() {
          _view = v;
          _focusedDay = DateTime.now();
        });
        Navigator.pop(context);
        _loadCurrentRange();
      },
    );
  }

  void _openAddTask(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => AddTaskSheet(
        initialDate: _focusedDay,
        onSaved: (task) {
          ref.read(tasksProvider.notifier).addTask(task);
        },
      ),
    );
  }
}
