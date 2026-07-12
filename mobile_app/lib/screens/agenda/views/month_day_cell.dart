import 'package:flutter/material.dart';
import 'package:table_calendar/table_calendar.dart';
import '../../../models/calendar_event.dart';
import '../../../models/person.dart';
import '../../../ui/task_color_utils.dart';

const _maxVisibleEvents = 3;

class MonthDayCell extends StatelessWidget {
  final DateTime day;
  final DateTime focusedMonth;
  final List<CalendarEvent> events;
  final Map<int, Person> personMap;
  final bool isSelected;
  final void Function(CalendarEvent) onEventTap;

  const MonthDayCell({
    super.key,
    required this.day,
    required this.focusedMonth,
    required this.events,
    required this.personMap,
    required this.isSelected,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final gridColor = theme.dividerColor.withValues(alpha: 0.7);
    final isOutside = day.month != focusedMonth.month;
    final isToday = isSameDay(day, DateTime.now());
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.45);

    final sorted = List<CalendarEvent>.from(events)
      ..sort((a, b) {
        final ta = a.startTime ?? '';
        final tb = b.startTime ?? '';
        final cmp = ta.compareTo(tb);
        return cmp != 0 ? cmp : a.title.compareTo(b.title);
      });

    final visible = sorted.take(_maxVisibleEvents).toList();
    final overflow = sorted.length - visible.length;

    return Container(
      decoration: BoxDecoration(
        border: Border(
          right: BorderSide(color: gridColor, width: 0.5),
          bottom: BorderSide(color: gridColor, width: 0.5),
        ),
      ),
      padding: const EdgeInsets.fromLTRB(2, 2, 2, 1),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            height: 22,
            child: Center(child: _dayNumber(context, isToday, isOutside, muted)),
          ),
          Expanded(
            child: ClipRect(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final event in visible)
                    _MonthEventChip(
                      event: event,
                      color: _eventColor(context, event, isOutside),
                      onTap: () => onEventTap(event),
                    ),
                  if (overflow > 0)
                    Padding(
                      padding: const EdgeInsets.only(top: 1, left: 2),
                      child: Text(
                        '+$overflow meer',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 9,
                          height: 1.1,
                          color: muted,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _dayNumber(
    BuildContext context,
    bool isToday,
    bool isOutside,
    Color muted,
  ) {
    final label = '${day.day}';
    if (isToday) {
      return Container(
        width: 24,
        height: 24,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary,
          shape: BoxShape.circle,
        ),
        child: Text(
          label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            height: 1,
          ),
        ),
      );
    }

    return Text(
      label,
      style: TextStyle(
        fontSize: 12,
        height: 1,
        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
        color: isOutside ? muted : Theme.of(context).colorScheme.onSurface,
      ),
    );
  }

  Color _eventColor(BuildContext context, CalendarEvent event, bool isOutside) {
    final base = personMap[event.personId]?.color ??
        Theme.of(context).colorScheme.primary;
    final adapted = adaptTaskColorForTheme(base, context);
    return isOutside ? adapted.withValues(alpha: 0.55) : adapted;
  }
}

class _MonthEventChip extends StatelessWidget {
  final CalendarEvent event;
  final Color color;
  final VoidCallback onTap;

  const _MonthEventChip({
    required this.event,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final textColor = contrastColorForBackground(color);

    return GestureDetector(
      onTap: onTap,
      child: Container(
      margin: const EdgeInsets.only(bottom: 1),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(3),
      ),
      child: Text(
        event.displayText,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: textColor,
          fontSize: 10,
          height: 1.2,
          fontWeight: FontWeight.w500,
        ),
      ),
      ),
    );
  }
}
