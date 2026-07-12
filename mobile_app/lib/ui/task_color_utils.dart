import 'package:flutter/material.dart';

Color contrastColorForBackground(Color background) =>
    background.computeLuminance() > 0.5 ? Colors.black : Colors.white;

Color adaptTaskColorForTheme(Color color, BuildContext context) {
  if (Theme.of(context).brightness != Brightness.dark) return color;
  final hsv = HSVColor.fromColor(color);
  return hsv
      .withSaturation((hsv.saturation * 0.85).clamp(0.0, 1.0))
      .withValue((hsv.value * 0.45).clamp(0.0, 1.0))
      .toColor();
}
