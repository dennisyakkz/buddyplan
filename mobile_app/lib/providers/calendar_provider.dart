import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/data_cache.dart';
import '../core/network_utils.dart';
import '../data/dashboard_repository.dart';
import '../data/sync_worker.dart';
import '../models/calendar_event.dart';
import '../providers/auth_provider.dart';

class CalendarState {
  final List<CalendarEvent> events;
  final bool isLoading;
  final String? error;
  final bool isOffline;
  final bool hasPendingMutations;

  const CalendarState({
    this.events = const [],
    this.isLoading = false,
    this.error,
    this.isOffline = false,
    this.hasPendingMutations = false,
  });

  List<CalendarEvent> eventsForDay(DateTime day) {
    return events.where((e) {
      return e.date.year == day.year &&
          e.date.month == day.month &&
          e.date.day == day.day;
    }).toList()
      ..sort((a, b) => (a.startTime ?? '').compareTo(b.startTime ?? ''));
  }
}

class CalendarNotifier extends Notifier<CalendarState> {
  @override
  CalendarState build() => const CalendarState();

  Future<DashboardRepository> _repo() => DashboardRepository.instance();

  Future<void> loadRange(DateTime start, DateTime end,
      {bool showLoading = true}) async {
    if (showLoading) {
      if (state.events.isEmpty) {
        final cached = await DataCache.calendarEventsForRange(start, end);
        state = CalendarState(
          events: cached,
          isLoading: true,
          isOffline: cached.isNotEmpty,
        );
      } else {
        state = CalendarState(
          events: state.events,
          isLoading: true,
          isOffline: state.isOffline,
        );
      }
    }
    try {
      ref.read(syncWorkerProvider)?.trigger();
      final s = _fmt(start);
      final e = _fmt(end);
      final raw = await ApiClient.instance.fetchCalendar(s, e);
      final events = raw
          .map((e) => CalendarEvent.fromJson(e as Map<String, dynamic>))
          .toList();
      await DataCache.mergeCalendarEvents(events, start, end);
      state = CalendarState(events: events);
    } catch (err) {
      if (isAuthError(err)) {
        ref.read(authProvider.notifier).handleSessionExpired();
        return;
      }
      if (isNetworkError(err)) {
        var cached = state.events;
        if (cached.isEmpty) {
          cached = await DataCache.calendarEventsForRange(start, end);
        }
        if (cached.isNotEmpty) {
          state = CalendarState(events: cached, isOffline: true);
          return;
        }
      }
      if (showLoading || state.events.isEmpty) {
        state = CalendarState(
          error: err.toString(),
          isOffline: isNetworkError(err),
        );
      } else {
        state = CalendarState(
          events: state.events,
          isOffline: isNetworkError(err),
        );
      }
    }
  }

  Future<void> addEventWithPayload({
    required Map<String, dynamic> apiPayload,
    required CalendarEvent optimistic,
  }) async {
    final repo = await _repo();
    await repo.createEventLocal(
      apiPayload: apiPayload,
      optimistic: optimistic,
    );
    state = CalendarState(
      events: [...state.events, optimistic],
      isOffline: true,
      hasPendingMutations: true,
    );
    ref.read(syncWorkerProvider)?.trigger();
    try {
      await repo.processOutbox();
    } catch (_) {}
  }

  void addEvent(CalendarEvent event) {
    state = CalendarState(
      events: [...state.events, event],
      isOffline: state.isOffline,
    );
  }

  void removeEvent(int id) {
    state = CalendarState(
      events: state.events.where((e) => e.id != id).toList(),
      isOffline: state.isOffline,
    );
  }

  String _fmt(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

final calendarProvider =
    NotifierProvider<CalendarNotifier, CalendarState>(CalendarNotifier.new);
