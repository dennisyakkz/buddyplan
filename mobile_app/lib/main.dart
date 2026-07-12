import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'core/preferences.dart';
import 'data/dashboard_repository.dart';
import 'data/sync_worker.dart';
import 'providers/auth_provider.dart';
import 'screens/main_screen.dart';
import 'screens/settings/settings_screen.dart';
import 'widgets/session_expired_listener.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppPreferences.init();
  await DashboardRepository.instance();
  await initializeDateFormatting('nl_NL');
  runApp(const ProviderScope(child: BuddyplanApp()));
}

class BuddyplanApp extends ConsumerWidget {
  const BuddyplanApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(syncWorkerProvider);
    return MaterialApp(
      title: 'Buddyplan',
      debugShowCheckedModeBanner: false,
      locale: const Locale('nl', 'NL'),
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('nl', 'NL'),
      ],
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF1565C0),
        useMaterial3: true,
      ),
      home: const SessionExpiredListener(child: _AppRouter()),
    );
  }
}

class _AppRouter extends ConsumerWidget {
  const _AppRouter();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    if (!auth.isLoggedIn) {
      return const SettingsScreen();
    }
    return const MainScreen();
  }
}
