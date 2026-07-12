import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/preferences.dart';
import '../../models/calendar_event.dart';
import '../../models/person.dart';
import '../../providers/calendar_provider.dart';
import '../../providers/persons_provider.dart';
import '../../widgets/person_settings_row.dart';
import '../../widgets/outlook_refresh_indicator.dart';
import '../settings/settings_screen.dart';
import 'views/planning_view.dart';
import 'views/day_view.dart';
import 'views/week_view.dart';
import 'views/month_view.dart';
import 'add_event_sheet.dart';
import 'event_detail_screen.dart';

enum AgendaView { planning, day, week, month }

class AgendaScreen extends ConsumerStatefulWidget {
  const AgendaScreen({super.key});

  @override
  ConsumerState<AgendaScreen> createState() => _AgendaScreenState();
}

class _AgendaScreenState extends ConsumerState<AgendaScreen> {
  AgendaView _view = AgendaView.planning;
  AgendaView? _returnView;
  DateTime _focusedDay = DateTime.now();
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _refreshTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) _refreshCurrentRange();
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadCurrentRange());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  void _loadCurrentRange() {
    final start = _rangeStart(_focusedDay);
    final end = _rangeEnd(_focusedDay);
    ref.read(calendarProvider.notifier).loadRange(start, end);
  }

  Future<void> _refreshCurrentRange() {
    final start = _rangeStart(_focusedDay);
    final end = _rangeEnd(_focusedDay);
    return ref
        .read(calendarProvider.notifier)
        .loadRange(start, end, showLoading: false);
  }

  DateTime _rangeStart(DateTime d) {
    switch (_view) {
      case AgendaView.planning:
        final now = DateTime.now();
        return DateTime(now.year, now.month, now.day);
      case AgendaView.day:
        return DateTime(d.year, d.month, d.day);
      case AgendaView.week:
        final mon = d.subtract(Duration(days: d.weekday - 1));
        return DateTime(mon.year, mon.month, mon.day);
      case AgendaView.month:
        return DateTime(d.year, d.month, 1);
    }
  }

  DateTime _rangeEnd(DateTime d) {
    switch (_view) {
      case AgendaView.planning:
        return DateTime(d.year, d.month + 2, 0);
      case AgendaView.day:
        return DateTime(d.year, d.month, d.day);
      case AgendaView.week:
        final mon = d.subtract(Duration(days: d.weekday - 1));
        return mon.add(const Duration(days: 6));
      case AgendaView.month:
        return DateTime(d.year, d.month + 1, 0);
    }
  }

  String get _viewLabel {
    switch (_view) {
      case AgendaView.planning:
        return 'Planning';
      case AgendaView.day:
        return 'Dag';
      case AgendaView.week:
        return 'Week';
      case AgendaView.month:
        return 'Maand';
    }
  }

  @override
  Widget build(BuildContext context) {
    final personsState = ref.watch(personsProvider);
    final calState = ref.watch(calendarProvider);
    final canManageAny =
        personsState.persons.any((p) => p.canManageAgenda);

    return PopScope(
      canPop: !(_view == AgendaView.day && _returnView != null),
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && _view == AgendaView.day && _returnView != null) {
          _popToPreviousView();
        }
      },
      child: Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        leading: (_view == AgendaView.day && _returnView != null)
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: _popToPreviousView,
                tooltip: 'Terug',
              )
            : null,
        title: Text(_viewLabel),
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
      endDrawer: _buildDrawer(context, personsState),
      body: _buildBody(calState, personsState),
      floatingActionButton: canManageAny
          ? FloatingActionButton(
              onPressed: () => _openAddEvent(context),
              child: const Icon(Icons.add),
            )
          : null,
    ),
    );
  }

  void _popToPreviousView() {
    final target = _returnView;
    if (target == null) return;
    setState(() {
      _view = target;
      _returnView = null;
    });
    _loadCurrentRange();
  }

  void _goToDay(DateTime day, {AgendaView? returnTo}) {
    setState(() {
      if (returnTo != null) _returnView = returnTo;
      _focusedDay = day;
      _view = AgendaView.day;
    });
    _loadCurrentRange();
  }

  Future<void> _openEvent(
    CalendarEvent event,
    List<Person> persons,
  ) async {
    var canManage = false;
    for (final p in persons) {
      if (p.id == event.personId) {
        canManage = p.canManageAgenda;
        break;
      }
    }
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => EventDetailScreen(
          listEvent: event,
          canManage: canManage,
        ),
      ),
    );
    if (changed == true) _loadCurrentRange();
  }

  Widget _buildBody(CalendarState calState, PersonsState personsState) {
    if (calState.isLoading && calState.events.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (calState.error != null && calState.events.isEmpty) {
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
              child: Text(calState.error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 13)),
            ),
            const SizedBox(height: 12),
            Center(
              child: ElevatedButton(
                  onPressed: _loadCurrentRange, child: const Text('Opnieuw')),
            ),
            Center(
              child: TextButton(
                onPressed: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => const SettingsScreen())),
                child: const Text('Instellingen'),
              ),
            ),
          ],
        ),
      );
    }

    final enabled = personsState.persons
        .where((p) => AppPreferences.isPersonEnabled(p.id))
        .toList();
    final filteredEvents = calState.events
        .where((e) => enabled.any((p) => p.id == e.personId))
        .toList();

    switch (_view) {
      case AgendaView.planning:
        return PlanningView(
          events: filteredEvents,
          persons: personsState.persons,
          startDate: _rangeStart(_focusedDay),
          endDate: _rangeEnd(_focusedDay),
          onRefresh: _refreshCurrentRange,
          onDayTap: (d) => _goToDay(d, returnTo: AgendaView.planning),
          onEventTap: (e) => _openEvent(e, personsState.persons),
        );
      case AgendaView.day:
        return DayView(
          events: filteredEvents,
          persons: personsState.persons,
          day: _focusedDay,
          onRefresh: _refreshCurrentRange,
          onEventTap: (e) => _openEvent(e, personsState.persons),
          onPrev: () => setState(() {
            _focusedDay = _focusedDay.subtract(const Duration(days: 1));
            _loadCurrentRange();
          }),
          onNext: () => setState(() {
            _focusedDay = _focusedDay.add(const Duration(days: 1));
            _loadCurrentRange();
          }),
        );
      case AgendaView.week:
        return WeekView(
          events: filteredEvents,
          persons: personsState.persons,
          anchorDay: _focusedDay,
          onRefresh: _refreshCurrentRange,
          onPrev: () => setState(() {
            _focusedDay = _focusedDay.subtract(const Duration(days: 7));
            _loadCurrentRange();
          }),
          onNext: () => setState(() {
            _focusedDay = _focusedDay.add(const Duration(days: 7));
            _loadCurrentRange();
          }),
          onDayTap: (d) => _goToDay(d, returnTo: AgendaView.week),
          onEventTap: (e) => _openEvent(e, personsState.persons),
        );
      case AgendaView.month:
        return MonthView(
          events: filteredEvents,
          persons: personsState.persons,
          focusedDay: _focusedDay,
          onRefresh: _refreshCurrentRange,
          onDaySelected: (d) => setState(() {
            _focusedDay = d;
            _loadCurrentRange();
          }),
          onPageChanged: (d) => setState(() {
            _focusedDay = d;
            _loadCurrentRange();
          }),
          onDayTap: (d) => _goToDay(d, returnTo: AgendaView.month),
          onEventTap: (e) => _openEvent(e, personsState.persons),
        );
    }
  }

  Widget _buildDrawer(BuildContext context, PersonsState personsState) {
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
            _viewTile(context, AgendaView.planning, Icons.view_agenda, 'Planning'),
            _viewTile(context, AgendaView.day, Icons.today, 'Dag'),
            _viewTile(context, AgendaView.week, Icons.view_week, 'Week'),
            _viewTile(context, AgendaView.month, Icons.calendar_month, 'Maand'),
            const Divider(),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
              child: Text('Kalenders',
                  style: Theme.of(context).textTheme.titleSmall),
            ),
            Expanded(
              child: personsState.isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView(
                      children: personsState.persons
                          .map((p) => PersonSettingsRow(person: p))
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
                        builder: (_) => const SettingsScreen()));
              },
            ),
          ],
        ),
      ),
    );
  }

  ListTile _viewTile(
      BuildContext context, AgendaView v, IconData icon, String label) {
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
          _returnView = null;
          _focusedDay = DateTime.now();
        });
        Navigator.pop(context);
        _loadCurrentRange();
      },
    );
  }

  void _openAddEvent(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => AddEventSheet(
        initialDate: _focusedDay,
        onSaved: (event) {
          ref.read(calendarProvider.notifier).addEvent(event);
        },
      ),
    );
  }
}
