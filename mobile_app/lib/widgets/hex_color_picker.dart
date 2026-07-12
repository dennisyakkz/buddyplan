import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

String colorToHex(Color color) {
  final rgb = color.toARGB32() & 0xFFFFFF;
  return '#${rgb.toRadixString(16).padLeft(6, '0').toUpperCase()}';
}

Color hexToColor(String hex) {
  final h = hex.replaceFirst('#', '');
  return Color(int.parse('FF$h', radix: 16));
}

Future<String?> showHexColorPickerDialog(
  BuildContext context, {
  required Color initialColor,
  String title = 'Kies kleur',
}) async {
  var picked = initialColor;

  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) {
      return StatefulBuilder(
        builder: (context, setState) {
          return AlertDialog(
            title: Text(title),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Snelle keuze',
                      style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  BlockPicker(
                    pickerColor: picked,
                    onColorChanged: (color) =>
                        setState(() => picked = color),
                    availableColors: pickerColors,
                  ),
                  const SizedBox(height: 16),
                  Text('Aangepast',
                      style: Theme.of(context).textTheme.labelLarge),
                  const SizedBox(height: 8),
                  ColorPicker(
                    pickerColor: picked,
                    onColorChanged: (color) =>
                        setState(() => picked = color),
                    enableAlpha: false,
                    displayThumbColor: true,
                    pickerAreaHeightPercent: 0.65,
                    portraitOnly: true,
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Annuleren'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Klaar'),
              ),
            ],
          );
        },
      );
    },
  );

  if (confirmed == true) return colorToHex(picked);
  return null;
}

/// Preset swatches plus a broad palette for custom selection.
const List<Color> pickerColors = [
  Color(0xFF1E88E5),
  Color(0xFF43A047),
  Color(0xFFE53935),
  Color(0xFFFB8C00),
  Color(0xFF8E24AA),
  Color(0xFF00ACC1),
  Color(0xFFE91E63),
  Color(0xFF795548),
  Color(0xFF3949AB),
  Color(0xFF00897B),
  Color(0xFFC0CA33),
  Color(0xFF6D4C41),
  Color(0xFF546E7A),
  Color(0xFFD81B60),
  Color(0xFF5E35B1),
  Color(0xFF039BE5),
  Color(0xFF7CB342),
  Color(0xFFF4511E),
  Color(0xFF757575),
  Color(0xFF000000),
];

class ColorDotButton extends StatelessWidget {
  final Color color;
  final VoidCallback onTap;
  final double radius;

  const ColorDotButton({
    super.key,
    required this.color,
    required this.onTap,
    this.radius = 16,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.all(4),
          child: CircleAvatar(
            backgroundColor: color,
            radius: radius,
          ),
        ),
      ),
    );
  }
}
