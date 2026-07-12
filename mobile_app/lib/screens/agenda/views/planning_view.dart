import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../models/calendar_event.dart';
import '../../../models/person.dart';

import '../../../widgets/outlook_refresh_indicator.dart';

class PlanningView extends StatelessWidget {
  final List<CalendarEvent> events;
  final List<Person> persons;
  final DateTime startDate;
  final DateTime endDate;
  final void Function(DateTime) onDayTap;
  final void Function(CalendarEvent) onEventTap;
  final Future<void> Function() onRefresh;

  const PlanningView({
    super.key,
    required this.events,
    required this.persons,
    required this.startDate,
    required this.endDate,
    required this.onDayTap,
    required this.onEventTap,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final grouped = <DateTime, List<CalendarEvent>>{};
    for (final e in events) {
      final day = DateTime(e.date.year, e.date.month, e.date.day);
      if (day.isBefore(today)) continue;
      grouped.putIfAbsent(day, () => []).add(e);
    }
    final days = grouped.keys.toList()..sort();

    if (days.isEmpty) {
      return OutlookRefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          physics: alwaysScrollable,
          children: const [
            SizedBox(height: 120),
            Center(child: Text('Geen items in dit bereik')),
          ],
        ),
      );
    }

    final personMap = {for (final p in persons) p.id: p};
    final dayFmt = DateFormat('EEEE d MMMM', 'nl_NL');

    return OutlookRefreshIndicator(
      onRefresh: onRefresh,
      child: ListView.builder(
        physics: alwaysScrollable,
        itemCount: days.length,
      itemBuilder: (context, index) {
        final day = days[index];
        final dayEvents = grouped[day]!
          ..sort((a, b) => (a.startTime ?? '').compareTo(b.startTime ?? ''));
        final isToday = _isToday(day);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              onTap: () => onDayTap(day),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
                child: Text(
                  dayFmt.format(day),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                    color: isToday
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).textTheme.titleMedium?.color,
                  ),
                ),
              ),
            ),
            ...dayEvents.map((e) {
              final person = personMap[e.personId];
              return _EventTile(
                event: e,
                color: person?.color,
                onTap: () => onEventTap(e),
              );
            }),
          ],
        );
      },
      ),
    );
  }

  bool _isToday(DateTime d) {
    final now = DateTime.now();
    return d.year == now.year && d.month == now.month && d.day == now.day;
  }
}

class _EventTile extends StatelessWidget {
  final CalendarEvent event;
  final Color? color;
  final VoidCallback onTap;

  const _EventTile({
    required this.event,
    this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
      padding: const EdgeInsets.fromLTRB(16, 2, 16, 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (event.startTime != null) ...[
            SizedBox(
              width: 52,
              child: Text(event.startTime!,
                  style: Theme.of(context).textTheme.bodySmall),
            ),
          ] else
            const SizedBox(width: 52),
          Container(
            width: 4,
            height: 36,
            margin: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: color ?? Theme.of(context).colorScheme.primary,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Expanded(
            child: Text(event.title,
                style: const TextStyle(fontSize: 14),
                maxLines: 2,
                overflow: TextOverflow.ellipsis),
          ),
        ],
      ),
      ),
    );
  }
}
