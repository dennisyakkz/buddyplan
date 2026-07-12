import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';

class SessionExpiredListener extends ConsumerStatefulWidget {
  const SessionExpiredListener({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<SessionExpiredListener> createState() =>
      _SessionExpiredListenerState();
}

class _SessionExpiredListenerState extends ConsumerState<SessionExpiredListener> {
  var _dialogVisible = false;

  @override
  Widget build(BuildContext context) {
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.sessionExpired && !_dialogVisible) {
        _dialogVisible = true;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          _showSessionExpiredDialog();
        });
      }
    });

    return widget.child;
  }

  Future<void> _showSessionExpiredDialog() async {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Sessie verlopen'),
        content: const Text('Sessie verlopen, u moet opnieuw inloggen.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
    if (!mounted) return;
    _dialogVisible = false;
    await ref.read(authProvider.notifier).dismissSessionExpired();
  }
}
