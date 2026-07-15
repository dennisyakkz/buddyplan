import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../models/calendar_event.dart';
import '../../../models/person.dart';
import '../../../ui/buddyplan_colors.dart';
import '../../../ui/color_palette.dart';
import '../../../widgets/outlook_refresh_indicator.dart';
import '../../../widgets/swipe_nav_detector.dart';

class WeekView extends StatelessWidget {
  final List<CalendarEvent> events;
  final List<Person> persons;
  final DateTime anchorDay;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final void Function(DateTime) onDayTap;
  final void Function(CalendarEvent) onEventTap;
  final Future<void> Function() onRefresh;

  const WeekView({
    super.key,
    required this.events,
    required this.persons,
    required this.anchorDay,
    required this.onPrev,
    required this.onNext,
    required this.onDayTap,
    required this.onEventTap,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final monday = anchorDay.subtract(Duration(days: anchorDay.weekday - 1));
    final days =
        List.generate(7, (i) => DateTime(monday.year, monday.month, monday.day + i));
    final personMap = {for (final p in persons) p.id: p};
    final dayFmt = DateFormat('d', 'nl_NL');
    final dayNameFmt = DateFormat('EEE', 'nl_NL');
    final monthFmt = DateFormat('MMMM yyyy', 'nl_NL');
    final now = DateTime.now();

    return SwipeNavDetector(
      onSwipeToPrevious: onPrev,
      onSwipeToNext: onNext,
      child: Column(
        children: [
          Row(children: [
            IconButton(onPressed: onPrev, icon: const Icon(Icons.chevron_left)),
            Expanded(
                child: Text(monthFmt.format(monday),
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontWeight: FontWeight.bold))),
            IconButton(
                onPressed: onNext, icon: const Icon(Icons.chevron_right)),
          ]),
          Row(
            children: days.map((d) {
              final isToday = d.year == now.year &&
                  d.month == now.month &&
                  d.day == now.day;
              return Expanded(
                child: InkWell(
                  onTap: () => onDayTap(d),
                  child: Column(
                    children: [
                      Text(dayNameFmt.format(d).toUpperCase(),
                          style: const TextStyle(fontSize: 11)),
                      Container(
                        margin: const EdgeInsets.symmetric(vertical: 2),
                        width: 28,
                        height: 28,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isToday
                              ? BuddyplanColors.teal
                              : Colors.transparent,
                        ),
                        child: Center(
                          child: Text(
                            dayFmt.format(d),
                            style: TextStyle(
                              color: isToday ? Colors.white : null,
                              fontWeight: isToday ? FontWeight.bold : null,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
          ),
          const Divider(height: 1),
          Expanded(
            child: OutlookRefreshIndicator(
              onRefresh: onRefresh,
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return SingleChildScrollView(
                    physics: alwaysScrollable,
                    child: ConstrainedBox(
                      constraints: BoxConstraints(minHeight: constraints.maxHeight),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: days.map((d) {
                          final dayEvents = events
                              .where((e) =>
                                  e.date.year == d.year &&
                                  e.date.month == d.month &&
                                  e.date.day == d.day)
                              .toList()
                            ..sort((a, b) =>
                                (a.startTime ?? '').compareTo(b.startTime ?? ''));
                          return Expanded(
                            child: Column(
                              children: dayEvents.map((e) {
                                final person = personMap[e.personId];
                                final chip = ColorPalette.chipStyle(
                                    context, person?.profileColor);
                                return InkWell(
                                  onTap: () => onEventTap(e),
                                  child: Container(
                                    margin: const EdgeInsets.all(1),
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 4, vertical: 3),
                                    decoration: BoxDecoration(
                                      color: chip.background,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        if (e.startTime != null)
                                          Text(
                                            e.startTime!,
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: chip.text,
                                            ),
                                          ),
                                        Text(
                                          e.title,
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: chip.text,
                                          ),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ],
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
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
