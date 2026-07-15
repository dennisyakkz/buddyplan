import 'package:flutter/material.dart';

class ChipStyle {
  final Color background;
  final Color text;

  const ChipStyle({required this.background, required this.text});
}

/// Brandbook §3 agenda/task color labels (light + dark pairs).
class ColorPalette {
  ColorPalette._();

  static const labels = [
    'rood',
    'oranje',
    'geel',
    'groen',
    'blauw',
    'teal',
    'paars',
    'bruin',
  ];

  static const _lightBg = {
    'rood': Color(0xFFFED7D7),
    'oranje': Color(0xFFFEEBC8),
    'geel': Color(0xFFFEFCBF),
    'groen': Color(0xFFC6F6D5),
    'blauw': Color(0xFFEBF8FF),
    'teal': Color(0xFFE6FFFA),
    'paars': Color(0xFFEBF4FF),
    'bruin': Color(0xFFEDF2F7),
  };

  static const _lightText = {
    'rood': Color(0xFF9B2C2C),
    'oranje': Color(0xFF9C4221),
    'geel': Color(0xFF744210),
    'groen': Color(0xFF22543D),
    'blauw': Color(0xFF2B6CB0),
    'teal': Color(0xFF234E52),
    'paars': Color(0xFF4C51BF),
    'bruin': Color(0xFF4A5568),
  };

  static const _darkBg = {
    'rood': Color(0xFF9B2C2C),
    'oranje': Color(0xFF9C4221),
    'geel': Color(0xFF744210),
    'groen': Color(0xFF22543D),
    'blauw': Color(0xFF2B6CB0),
    'teal': Color(0xFF234E52),
    'paars': Color(0xFF4C51BF),
    'bruin': Color(0xFF4A5568),
  };

  static const _darkText = {
    'rood': Color(0xFFFFF5F5),
    'oranje': Color(0xFFFFFAF0),
    'geel': Color(0xFFFFFFF0),
    'groen': Color(0xFFF0FFF4),
    'blauw': Color(0xFFEBF8FF),
    'teal': Color(0xFFE6FFFA),
    'paars': Color(0xFFEBF4FF),
    'bruin': Color(0xFFF7FAFC),
  };

  static String normalizeLabel(String? value) {
    if (value == null || value.trim().isEmpty) return 'teal';
    final lowered = value.trim().toLowerCase();
    if (labels.contains(lowered)) return lowered;
    return 'teal';
  }

  static ChipStyle chipStyle(BuildContext context, String? label) {
    final key = normalizeLabel(label);
    final dark = Theme.of(context).brightness == Brightness.dark;
    if (dark) {
      return ChipStyle(
        background: _darkBg[key] ?? _darkBg['teal']!,
        text: _darkText[key] ?? _darkText['teal']!,
      );
    }
    return ChipStyle(
      background: _lightBg[key] ?? _lightBg['teal']!,
      text: _lightText[key] ?? _lightText['teal']!,
    );
  }

  /// Accent for task indicator lines and checkbox rings.
  static Color accentColor(BuildContext context, String? label) {
    return chipStyle(context, label).text;
  }

  static Color dotColor(BuildContext context, String? label) {
    return chipStyle(context, label).text;
  }
}
