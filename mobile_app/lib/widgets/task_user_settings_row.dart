import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/task_users_provider.dart';
import 'hex_color_picker.dart';

class TaskUserSettingsRow extends ConsumerWidget {
  final TaskUser user;
  final bool showDivider;

  const TaskUserSettingsRow({
    super.key,
    required this.user,
    this.showDivider = true,
  });

  Future<void> _pickColor(BuildContext context, WidgetRef ref) async {
    final hex = await showHexColorPickerDialog(
      context,
      initialColor: user.color,
      title: 'Kleur voor ${user.name}',
    );
    if (hex != null) {
      await ref.read(taskUsersProvider.notifier).setColor(user.id, hex);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(taskUsersProvider.notifier);
    final enabled = notifier.isEnabled(user.id);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
          child: Row(
            children: [
              ColorDotButton(
                color: user.color,
                onTap: () => _pickColor(context, ref),
              ),
              const SizedBox(width: 8),
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
