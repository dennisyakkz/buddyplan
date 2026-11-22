import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/ai_provider.dart';
import '../../providers/connection_provider.dart';
import '../../providers/persons_provider.dart';
import '../../providers/task_users_provider.dart';
import '../../widgets/offline_banner.dart';
import 'agenda/agenda_screen.dart';
import 'ai/ai_chat_screen.dart';
import 'tasks/tasks_screen.dart';

class MainScreen extends ConsumerStatefulWidget {
  const MainScreen({super.key});

  @override
  ConsumerState<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends ConsumerState<MainScreen>
    with WidgetsBindingObserver {
  int _currentIndex = 0;
  Timer? _aiStatusTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    // Load persons after first frame so providers are ready.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(personsProvider.notifier).load();
      ref.read(taskUsersProvider.notifier).load();
      ref.read(aiConfiguredProvider.notifier).refresh();
    });
    // REQ-MOB-050: follow the backend setting with the automatic refresh (REQ-MOB-032).
    _aiStatusTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) ref.read(aiConfiguredProvider.notifier).refresh();
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _aiStatusTimer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && mounted) {
      ref.read(aiConfiguredProvider.notifier).refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isOffline = ref.watch(isOfflineProvider);
    final aiConfigured = ref.watch(aiConfiguredProvider);
    final index = clampTab(_currentIndex, aiConfigured: aiConfigured);
    if (index != _currentIndex) {
      // The AI buddy tab disappeared while it was open: go to Agenda.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) setState(() => _currentIndex = index);
      });
    }

    return Scaffold(
      body: IndexedStack(
        index: index,
        children: [
          const AgendaScreen(),
          const TasksScreen(),
          if (aiConfigured) const AiChatScreen(),
        ],
      ),
      bottomNavigationBar: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (isOffline) const OfflineBanner(),
          NavigationBar(
            selectedIndex: index,
            onDestinationSelected: (i) => setState(() => _currentIndex = i),
            destinations: [
              const NavigationDestination(
                icon: Icon(Icons.calendar_month_outlined),
                selectedIcon: Icon(Icons.calendar_month),
                label: 'Agenda',
              ),
              const NavigationDestination(
                icon: Icon(Icons.checklist_outlined),
                selectedIcon: Icon(Icons.checklist),
                label: 'Taken',
              ),
              if (aiConfigured)
                const NavigationDestination(
                  icon: Icon(Icons.chat_bubble_outline),
                  selectedIcon: Icon(Icons.chat_bubble),
                  label: 'AI buddy',
                ),
            ],
          ),
        ],
      ),
    );
  }
}
