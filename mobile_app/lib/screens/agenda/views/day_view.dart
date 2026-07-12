import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../models/calendar_event.dart';
import '../../../models/person.dart';
import '../../../widgets/outlook_refresh_indicator.dart';
import '../../../widgets/swipe_nav_detector.dart';

class DayView extends StatelessWidget {
  final List<CalendarEvent> events;
  final List<Person> persons;
  final DateTime day;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final Future<void> Function() onRefresh;
  final void Function(CalendarEvent) onEventTap;

  const DayView({
    super.key,
    required this.events,
    required this.persons,
    required this.day,
    required this.onPrev,
    required this.onNext,
    required this.onRefresh,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    final dayFmt = DateFormat('EEEE d MMMM yyyy', 'nl_NL');
    final personMap = {for (final p in persons) p.id: p};
    final dayEvents = events
        .where((e) =>
            e.date.year == day.year &&
            e.date.month == day.month &&
            e.date.day == day.day)
        .toList()
      ..sort((a, b) => (a.startTime ?? '').compareTo(b.startTime ?? ''));

    return SwipeNavDetector(
      onSwipeToPrevious: onPrev,
      onSwipeToNext: onNext,
      child: Column(
      children: [
        Row(
          children: [
            IconButton(
                onPressed: onPrev, icon: const Icon(Icons.chevron_left)),
            Expanded(
              child: Text(dayFmt.format(day),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
            IconButton(
                onPressed: onNext, icon: const Icon(Icons.chevron_right)),
          ],
        ),
        const Divider(height: 1),
        Expanded(
          child: OutlookRefreshIndicator(
            onRefresh: onRefresh,
            child: dayEvents.isEmpty
                ? ListView(
                    physics: alwaysScrollable,
                    children: const [
                      SizedBox(height: 120),
                      Center(child: Text('Geen items')),
                    ],
                  )
                : ListView.separated(
                    physics: alwaysScrollable,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: dayEvents.length,
                    separatorBuilder: (_, __) =>
                        const Divider(height: 1, indent: 72),
                    itemBuilder: (context, i) {
                      final e = dayEvents[i];
                      final person = personMap[e.personId];
                      return ListTile(
                        onTap: () => onEventTap(e),
                        leading: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 4,
                              height: 48,
                              color: person?.color ??
                                  Theme.of(context).colorScheme.primary,
                            ),
                            const SizedBox(width: 8),
                            SizedBox(
                              width: 40,
                              child: Text(
                                e.startTime ?? '',
                                style: const TextStyle(fontSize: 12),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ],
                        ),
                        title: Text(e.title),
                        subtitle: e.endTime != null
                            ? Text('tot ${e.endTime}',
                                style: const TextStyle(fontSize: 12))
                            : null,
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
