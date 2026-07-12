import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../../models/calendar_event.dart';
import '../../../models/person.dart';
import '../../../widgets/outlook_refresh_indicator.dart';
import 'month_day_cell.dart';

class MonthView extends StatelessWidget {
  final List<CalendarEvent> events;
  final List<Person> persons;
  final DateTime focusedDay;
  final void Function(DateTime) onDaySelected;
  final void Function(DateTime) onPageChanged;
  final void Function(DateTime) onDayTap;
  final void Function(CalendarEvent) onEventTap;
  final Future<void> Function() onRefresh;

  const MonthView({
    super.key,
    required this.events,
    required this.persons,
    required this.focusedDay,
    required this.onDaySelected,
    required this.onPageChanged,
    required this.onDayTap,
    required this.onEventTap,
    required this.onRefresh,
  });

  List<CalendarEvent> _eventsForDay(DateTime day) {
    return events.where((e) {
      return e.date.year == day.year &&
          e.date.month == day.month &&
          e.date.day == day.day;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final personMap = {for (final p in persons) p.id: p};
    final theme = Theme.of(context);
    final gridColor = theme.dividerColor.withValues(alpha: 0.7);

    return OutlookRefreshIndicator(
      onRefresh: onRefresh,
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            physics: alwaysScrollable,
            child: ConstrainedBox(
              constraints: BoxConstraints(minHeight: constraints.maxHeight),
              child: SizedBox(
                height: constraints.maxHeight,
                child: TableCalendar<CalendarEvent>(
                  locale: 'nl_NL',
                  firstDay: DateTime.utc(2020, 1, 1),
                  lastDay: DateTime.utc(2030, 12, 31),
                  focusedDay: focusedDay,
                  currentDay: DateTime.now(),
                  startingDayOfWeek: StartingDayOfWeek.monday,
                  calendarFormat: CalendarFormat.month,
                  availableCalendarFormats: const {
                    CalendarFormat.month: 'Maand',
                  },
                  availableGestures: AvailableGestures.horizontalSwipe,
                  headerVisible: true,
                  daysOfWeekVisible: true,
                  shouldFillViewport: true,
                  sixWeekMonthsEnforced: true,
                  pageAnimationEnabled: true,
                  eventLoader: _eventsForDay,
                  onDaySelected: (selected, focused) {
                    onDaySelected(selected);
                    onDayTap(selected);
                  },
                  onPageChanged: onPageChanged,
                  selectedDayPredicate: (d) => isSameDay(d, focusedDay),
                  headerStyle: HeaderStyle(
                    formatButtonVisible: false,
                    titleCentered: false,
                    leftChevronPadding: const EdgeInsets.all(8),
                    rightChevronPadding: const EdgeInsets.all(8),
                    headerPadding: const EdgeInsets.symmetric(vertical: 4),
                    titleTextFormatter: (date, locale) =>
                        DateFormat.yMMMM('nl_NL').format(date),
                    titleTextStyle: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ) ??
                        const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                  ),
                  daysOfWeekHeight: 28,
                  daysOfWeekStyle: DaysOfWeekStyle(
                    dowTextFormatter: (date, locale) {
                      final label = DateFormat('EEE', 'nl_NL').format(date);
                      if (label.isEmpty) return label;
                      return label[0].toUpperCase() +
                          label.substring(1).replaceAll('.', '');
                    },
                    weekdayStyle: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                    ),
                    weekendStyle: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                    ),
                  ),
                  calendarStyle: CalendarStyle(
                    outsideDaysVisible: true,
                    cellMargin: EdgeInsets.zero,
                    cellPadding: EdgeInsets.zero,
                    isTodayHighlighted: false,
                    tableBorder: TableBorder(
                      left: BorderSide(color: gridColor, width: 0.5),
                      top: BorderSide(color: gridColor, width: 0.5),
                      horizontalInside: BorderSide.none,
                      verticalInside: BorderSide.none,
                    ),
                    defaultTextStyle: const TextStyle(fontSize: 12),
                    outsideTextStyle: TextStyle(
                      fontSize: 12,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.45),
                    ),
                  ),
                  calendarBuilders: CalendarBuilders(
                    prioritizedBuilder: (context, day, focusedMonth) {
                      return MonthDayCell(
                        day: day,
                        focusedMonth: focusedMonth,
                        events: _eventsForDay(day),
                        personMap: personMap,
                        isSelected: isSameDay(day, focusedDay),
                        onEventTap: onEventTap,
                      );
                    },
                    markerBuilder: (context, day, dayEvents) =>
                        const SizedBox.shrink(),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
