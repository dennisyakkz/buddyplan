import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../models/task_item.dart';
import '../../../models/person.dart';
import '../../../ui/buddyplan_colors.dart';
import '../../../widgets/outlook_refresh_indicator.dart';
import '../../../widgets/swipe_nav_detector.dart';
import '../../../widgets/task_tile.dart';

class WeekTasksView extends StatelessWidget {
  final List<DateTime> days;
  final List<TaskItem> Function(DateTime) tasksForDay;
  final List<Person> persons;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final Set<int> manageableIds;
  final void Function(TaskItem) onComplete;
  final void Function(TaskItem) onOpen;
  final Future<void> Function() onRefresh;

  const WeekTasksView({
    super.key,
    required this.days,
    required this.tasksForDay,
    required this.persons,
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
    final dayFmt = DateFormat('EEE d MMM', 'nl_NL');
    final monthFmt = DateFormat('MMMM yyyy', 'nl_NL');
    final now = DateTime.now();

    return SwipeNavDetector(
      onSwipeToPrevious: onPrev,
      onSwipeToNext: onNext,
      child: Column(
      children: [
        Row(children: [
          IconButton(
              onPressed: onPrev, icon: const Icon(Icons.chevron_left)),
          Expanded(
              child: Text(monthFmt.format(days.first),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontWeight: FontWeight.bold))),
          IconButton(
              onPressed: onNext, icon: const Icon(Icons.chevron_right)),
        ]),
        const Divider(height: 1),
        Expanded(
          child: OutlookRefreshIndicator(
            onRefresh: onRefresh,
            child: ListView.builder(
              physics: alwaysScrollable,
              itemCount: days.length,
              itemBuilder: (context, i) {
                final day = days[i];
                final dayTasks = tasksForDay(day);
                final isToday = day.year == now.year &&
                    day.month == now.month &&
                    day.day == now.day;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                      child: Text(
                        dayFmt.format(day),
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: isToday
                              ? BuddyplanColors.teal
                              : null,
                        ),
                      ),
                    ),
                    if (dayTasks.isEmpty)
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 0, 16, 4),
                        child: Text('—',
                            style:
                                TextStyle(color: Colors.grey, fontSize: 13)),
                      )
                    else
                      ...dayTasks.map((task) {
                        final profileColor =
                            personMap[task.personId]?.profileColor;
                        return TaskTile(
                          task: task,
                          profileColor: profileColor,
                          dense: true,
                          canComplete: manageableIds.contains(task.personId),
                          onComplete: () => onComplete(task),
                          onOpen: () => onOpen(task),
                        );
                      }),
                    const Divider(height: 1),
                  ],
                );
              },
            ),
          ),
        ),
      ],
      ),
    );
  }
}
