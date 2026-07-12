import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../models/task_item.dart';
import '../../../models/person.dart';
import '../../../widgets/outlook_refresh_indicator.dart';
import '../../../widgets/swipe_nav_detector.dart';
import '../../../widgets/task_tile.dart';

class DayTasksView extends StatelessWidget {
  final List<TaskItem> tasks;
  final List<Person> persons;
  final DateTime day;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final Set<int> manageableIds;
  final void Function(TaskItem) onComplete;
  final void Function(TaskItem) onOpen;
  final Future<void> Function() onRefresh;

  const DayTasksView({
    super.key,
    required this.tasks,
    required this.persons,
    required this.day,
    required this.onPrev,
    required this.onNext,
    required this.onComplete,
    required this.onOpen,
    required this.onRefresh,
    required this.manageableIds,
  });

  @override
  Widget build(BuildContext context) {
    final personMap = {for (final p in persons) p.id: p};
    final fmt = DateFormat('EEEE d MMMM yyyy', 'nl_NL');

    return SwipeNavDetector(
      onSwipeToPrevious: onPrev,
      onSwipeToNext: onNext,
      child: Column(
      children: [
        Row(children: [
          IconButton(onPressed: onPrev, icon: const Icon(Icons.chevron_left)),
          Expanded(
              child: Text(fmt.format(day),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontWeight: FontWeight.bold))),
          IconButton(
              onPressed: onNext, icon: const Icon(Icons.chevron_right)),
        ]),
        const Divider(height: 1),
        Expanded(
          child: OutlookRefreshIndicator(
            onRefresh: onRefresh,
            child: tasks.isEmpty
                ? ListView(
                    physics: alwaysScrollable,
                    children: const [
                      SizedBox(height: 120),
                      Center(child: Text('Geen taken')),
                    ],
                  )
                : ListView.builder(
                    physics: alwaysScrollable,
                    itemCount: tasks.length,
                    itemBuilder: (context, i) => TaskTile(
                      task: tasks[i],
                      personColor: personMap[tasks[i].personId]?.color,
                      canComplete: manageableIds.contains(tasks[i].personId),
                      onComplete: () => onComplete(tasks[i]),
                      onOpen: () => onOpen(tasks[i]),
                    ),
                  ),
          ),
        ),
      ],
      ),
    );
  }
}
