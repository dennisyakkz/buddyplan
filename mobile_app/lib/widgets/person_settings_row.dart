import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/person.dart';
import '../providers/persons_provider.dart';
import '../ui/color_palette.dart';

class PersonSettingsRow extends ConsumerWidget {
  final Person person;
  final bool showDivider;

  const PersonSettingsRow({
    super.key,
    required this.person,
    this.showDivider = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(personsProvider.notifier);
    final enabled = notifier.isEnabled(person.id);
    final label = person.isMe ? 'Mijn kalender' : person.name;
    final dotColor = ColorPalette.dotColor(context, person.profileColor);

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
                  label,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Switch(
                value: enabled,
                onChanged: (v) => notifier.setEnabled(person.id, v),
              ),
            ],
          ),
        ),
        if (showDivider) const Divider(height: 1),
      ],
    );
  }
}
