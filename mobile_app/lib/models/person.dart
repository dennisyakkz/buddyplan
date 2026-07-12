import 'package:flutter/material.dart';

class Person {
  final int id;
  final String name;
  final bool isMe;
  final Color color;
  final bool canManageAgenda;

  const Person({
    required this.id,
    required this.name,
    required this.isMe,
    required this.color,
    this.canManageAgenda = false,
  });

  factory Person.fromJson(Map<String, dynamic> json, {Color? overrideColor}) {
    final hexColor = (json['color'] as String?) ?? '#1E88E5';
    return Person(
      id: json['id'] as int,
      name: json['name'] as String,
      isMe: (json['is_me'] as bool?) ?? false,
      color: overrideColor ?? _hexToColor(hexColor),
      canManageAgenda: (json['can_manage_agenda'] as bool?) ?? false,
    );
  }

  static Color _hexToColor(String hex) {
    final h = hex.replaceFirst('#', '');
    return Color(int.parse('FF$h', radix: 16));
  }
}
