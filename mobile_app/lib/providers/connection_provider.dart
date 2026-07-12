import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'calendar_provider.dart';
import 'tasks_provider.dart';

final isOfflineProvider = Provider<bool>((ref) {
  final cal = ref.watch(calendarProvider);
  final tasks = ref.watch(tasksProvider);
  return cal.isOffline || tasks.isOffline;
});
