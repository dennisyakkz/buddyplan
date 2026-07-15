import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/task_users_provider.dart';
import '../ui/color_palette.dart';

class TaskUserSettingsRow extends ConsumerWidget {
  final TaskUser user;
  final bool showDivider;

  const TaskUserSettingsRow({
    super.key,
    required this.user,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(taskUsersProvider.notifier);
    final enabled = notifier.isEnabled(user.id);
    final dotColor = ColorPalette.dotColor(context, user.profileColor);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
          child: Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: dotColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  user.name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Switch(
                value: enabled,
                onChanged: (v) => notifier.setEnabled(user.id, v),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1),
      ],
    );
  }
}
