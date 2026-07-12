import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/person.dart';
import '../providers/persons_provider.dart';
import 'hex_color_picker.dart';

class PersonSettingsRow extends ConsumerWidget {
  final Person person;
  final bool showDivider;

  const PersonSettingsRow({
    super.key,
    required this.person,
    this.showDivider = true,
  });

  Future<void> _pickColor(BuildContext context, WidgetRef ref) async {
    final hex = await showHexColorPickerDialog(
      context,
      initialColor: person.color,
      title: 'Kleur voor ${person.isMe ? 'Mijn kalender' : person.name}',
    );
    if (hex != null) {
      await ref.read(personsProvider.notifier).setColor(person.id, hex);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(personsProvider.notifier);
    final enabled = notifier.isEnabled(person.id);
    final label = person.isMe ? 'Mijn kalender' : person.name;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
          child: Row(
            children: [
              ColorDotButton(
                color: person.color,
                onTap: () => _pickColor(context, ref),
              ),
              const SizedBox(width: 8),
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
