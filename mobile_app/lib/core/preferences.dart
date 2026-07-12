import 'dart:convert';
import 'dart:math';
import 'package:shared_preferences/shared_preferences.dart';

const _keyServerUrl = 'server_url';
const _keyAuthToken = 'auth_token';
const _keyLoggedInName = 'logged_in_name';
const _keyDeviceId = 'device_id';
const _keyPersonColors = 'person_colors';
const _keyPersonEnabled = 'person_enabled';
const _keyTaskPersonColors = 'task_person_colors';
const _keyTaskPersonEnabled = 'task_person_enabled';

const List<String> defaultColors = [
  '#1E88E5', '#43A047', '#E53935', '#FB8C00',
  '#8E24AA', '#00ACC1', '#E91E63', '#795548',
];

class AppPreferences {
  static SharedPreferences? _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static SharedPreferences get _p {
    assert(_prefs != null, 'AppPreferences.init() must be called first');
    return _prefs!;
  }

  static String get serverUrl =>
      (_p.getString(_keyServerUrl) ?? '').replaceAll(RegExp(r'/+$'), '');

  static Future<void> setServerUrl(String url) =>
      _p.setString(_keyServerUrl, url.replaceAll(RegExp(r'/+$'), ''));

  static String? get authToken => _p.getString(_keyAuthToken);

  static Future<void> setAuthToken(String? token) async {
    if (token == null) {
      await _p.remove(_keyAuthToken);
    } else {
      await _p.setString(_keyAuthToken, token);
    }
  }

  static String? get loggedInName => _p.getString(_keyLoggedInName);

  static Future<void> setLoggedInName(String? name) async {
    if (name == null) {
      await _p.remove(_keyLoggedInName);
    } else {
      await _p.setString(_keyLoggedInName, name);
    }
  }

  static String get deviceId {
    var id = _p.getString(_keyDeviceId);
    if (id == null || id.isEmpty) {
      id = _generateUuid();
      _p.setString(_keyDeviceId, id);
    }
    return id;
  }

  static String _generateUuid() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    String hex(int value) => value.toRadixString(16).padLeft(2, '0');
    return '${bytes.sublist(0, 4).map(hex).join()}-'
        '${bytes.sublist(4, 6).map(hex).join()}-'
        '${bytes.sublist(6, 8).map(hex).join()}-'
        '${bytes.sublist(8, 10).map(hex).join()}-'
        '${bytes.sublist(10, 16).map(hex).join()}';
  }

  static Map<int, String> get personColors {
    final raw = _p.getString(_keyPersonColors);
    if (raw == null) return {};
    final map = jsonDecode(raw) as Map<String, dynamic>;
    return map.map((k, v) => MapEntry(int.parse(k), v as String));
  }

  static Future<void> setPersonColors(Map<int, String> colors) =>
      _p.setString(_keyPersonColors,
          jsonEncode(colors.map((k, v) => MapEntry(k.toString(), v))));

  static Map<int, bool> get personEnabled {
    final raw = _p.getString(_keyPersonEnabled);
    if (raw == null) return {};
    final map = jsonDecode(raw) as Map<String, dynamic>;
    return map.map((k, v) => MapEntry(int.parse(k), v as bool));
  }

  static Future<void> setPersonEnabled(Map<int, bool> enabled) =>
      _p.setString(_keyPersonEnabled,
          jsonEncode(enabled.map((k, v) => MapEntry(k.toString(), v))));

  static bool isPersonEnabled(int id) => personEnabled[id] ?? true;

  static String colorForPerson(int id, int index) =>
      personColors[id] ?? defaultColors[index % defaultColors.length];

  static Future<void> ensureDefaultColors(List<MapEntry<int, int>> indexed) async {
    final existing = personColors;
    var changed = false;
    for (final e in indexed) {
      if (!existing.containsKey(e.key)) {
        existing[e.key] = defaultColors[e.value % defaultColors.length];
        changed = true;
      }
    }
    if (changed) await setPersonColors(existing);
  }

  static Map<int, String> get taskPersonColors {
    final raw = _p.getString(_keyTaskPersonColors);
    if (raw == null) return {};
    final map = jsonDecode(raw) as Map<String, dynamic>;
    return map.map((k, v) => MapEntry(int.parse(k), v as String));
  }

  static Future<void> setTaskPersonColors(Map<int, String> colors) =>
      _p.setString(_keyTaskPersonColors,
          jsonEncode(colors.map((k, v) => MapEntry(k.toString(), v))));

  static Map<int, bool> get taskPersonEnabled {
    final raw = _p.getString(_keyTaskPersonEnabled);
    if (raw == null) return {};
    final map = jsonDecode(raw) as Map<String, dynamic>;
    return map.map((k, v) => MapEntry(int.parse(k), v as bool));
  }

  static Future<void> setTaskPersonEnabled(Map<int, bool> enabled) =>
      _p.setString(_keyTaskPersonEnabled,
          jsonEncode(enabled.map((k, v) => MapEntry(k.toString(), v))));

  static bool isTaskPersonEnabled(int id) => taskPersonEnabled[id] ?? true;

  static String colorForTaskPerson(int id, int index) =>
      taskPersonColors[id] ?? defaultColors[index % defaultColors.length];

  static const _keyCalendarCache = 'calendar_cache_json';
  static const _keyTasksCache = 'tasks_cache_json';

  static String? get calendarCacheJson => _p.getString(_keyCalendarCache);

  static Future<void> setCalendarCacheJson(String json) =>
      _p.setString(_keyCalendarCache, json);

  static String? get tasksCacheJson => _p.getString(_keyTasksCache);

  static Future<void> setTasksCacheJson(String json) =>
      _p.setString(_keyTasksCache, json);

  static Future<void> clearDataCache() async {
    await _p.remove(_keyCalendarCache);
    await _p.remove(_keyTasksCache);
  }

  static Future<void> ensureDefaultTaskColors(
      List<MapEntry<int, int>> indexed) async {
    final existing = taskPersonColors;
    var changed = false;
    for (final e in indexed) {
      if (!existing.containsKey(e.key)) {
        existing[e.key] = defaultColors[e.value % defaultColors.length];
        changed = true;
      }
    }
    if (changed) await setTaskPersonColors(existing);
  }
}
