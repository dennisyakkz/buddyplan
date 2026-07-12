import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/connection_provider.dart';
import '../../providers/persons_provider.dart';
import '../../providers/task_users_provider.dart';
import '../../widgets/offline_banner.dart';
import 'agenda/agenda_screen.dart';
import 'tasks/tasks_screen.dart';

class MainScreen extends ConsumerStatefulWidget {
  const MainScreen({super.key});

  @override
  ConsumerState<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends ConsumerState<MainScreen> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    // Load persons after first frame so providers are ready.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(personsProvider.notifier).load();
      ref.read(taskUsersProvider.notifier).load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final isOffline = ref.watch(isOfflineProvider);

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: const [
          AgendaScreen(),
          TasksScreen(),
        ],
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isOffline) const OfflineBanner(),
          NavigationBar(
            selectedIndex: _currentIndex,
            onDestinationSelected: (i) => setState(() => _currentIndex = i),
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.calendar_month_outlined),
                selectedIcon: Icon(Icons.calendar_month),
                label: 'Agenda',
              ),
              NavigationDestination(
                icon: Icon(Icons.checklist_outlined),
                selectedIcon: Icon(Icons.checklist),
                label: 'Taken',
              ),
            ],
          ),
        ],
      ),
    );
  }
}
