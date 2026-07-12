import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'dashboard_repository.dart';

class SyncWorker with WidgetsBindingObserver {
  SyncWorker(this._repo);

  final DashboardRepository _repo;
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  var _started = false;

  Future<void> start() async {
    if (_started) return;
    _started = true;
    WidgetsBinding.instance.addObserver(this);
    _connectivitySub = Connectivity().onConnectivityChanged.listen((_) {
      _process();
    });
    await _process();
  }

  void stop() {
    _started = false;
    WidgetsBinding.instance.removeObserver(this);
    _connectivitySub?.cancel();
    _connectivitySub = null;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _process();
    }
  }

  Future<void> trigger() => _process();

  Future<void> _process() async {
    await _repo.processOutbox();
  }
}

final dashboardRepositoryProvider =
    FutureProvider<DashboardRepository>((ref) async {
  return DashboardRepository.instance();
});

final syncWorkerProvider = Provider<SyncWorker?>((ref) {
  final repoAsync = ref.watch(dashboardRepositoryProvider);
  return repoAsync.maybeWhen(
    data: (repo) {
      final worker = SyncWorker(repo);
      worker.start();
      ref.onDispose(worker.stop);
      return worker;
    },
    orElse: () => null,
  );
});
