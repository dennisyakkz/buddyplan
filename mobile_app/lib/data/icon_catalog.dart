import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/icon_catalog_entry.dart';
import '../ui/material_task_icon.dart';

class IconCatalog {
  IconCatalog._();

  static List<IconCatalogEntry>? _cache;
  static Future<List<IconCatalogEntry>>? _loading;

  static Future<List<IconCatalogEntry>> load() {
    return _loading ??= _load();
  }

  static Future<List<IconCatalogEntry>> _load() async {
    if (_cache != null) return _cache!;
    final raw = await rootBundle.loadString('assets/data/material-icons.json');
    final list = jsonDecode(raw) as List<dynamic>;
    _cache = list
        .map((e) => IconCatalogEntry.fromJson(e as Map<String, dynamic>))
        .toList();
    return _cache!;
  }

  static String labelFor(String? iconId, {List<IconCatalogEntry>? catalog}) {
    final id = MaterialTaskIcon.normalize(iconId);
    final entries = catalog ?? _cache;
    if (entries != null) {
      for (final e in entries) {
        if (e.id == id) return e.label;
      }
    }
    if (id.startsWith('md:')) return id.substring(3).replaceAll('_', ' ');
    if (id.startsWith('custom:')) return id.substring(7).replaceAll('-', ' ');
    return id;
  }

  static List<IconCatalogEntry> filter(
    List<IconCatalogEntry> catalog,
    String query, {
    int unfilteredLimit = 120,
  }) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) {
      return catalog.length <= unfilteredLimit
          ? catalog
          : catalog.sublist(0, unfilteredLimit);
    }
    return catalog.where((e) => e.searchText.contains(q)).toList();
  }
}
