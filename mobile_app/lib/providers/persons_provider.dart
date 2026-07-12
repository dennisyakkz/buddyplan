import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/preferences.dart';
import '../models/person.dart';

class PersonsState {
  final List<Person> persons;
  final bool isLoading;
  final String? error;

  const PersonsState({
    this.persons = const [],
    this.isLoading = false,
    this.error,
  });
}

class PersonsNotifier extends Notifier<PersonsState> {
  @override
  PersonsState build() => const PersonsState(isLoading: true);

  Future<void> load() async {
    state = const PersonsState(isLoading: true);
    try {
      final raw = await ApiClient.instance.fetchPersons();
      final indexed = raw
          .asMap()
          .entries
          .map((e) => MapEntry(
              (e.value as Map<String, dynamic>)['id'] as int, e.key))
          .toList();
      await AppPreferences.ensureDefaultColors(indexed);
      final colors = AppPreferences.personColors;
      final persons = raw.asMap().entries.map((e) {
        final json = e.value as Map<String, dynamic>;
        final id = json['id'] as int;
        final storedHex = colors[id];
        Color? c;
        if (storedHex != null) {
          final h = storedHex.replaceFirst('#', '');
          c = Color(int.parse('FF$h', radix: 16));
        }
        return Person.fromJson(json, overrideColor: c);
      }).toList();
      state = PersonsState(persons: persons);
    } catch (e) {
      state = PersonsState(error: e.toString());
    }
  }

  bool isEnabled(int personId) => AppPreferences.isPersonEnabled(personId);

  Future<void> setEnabled(int personId, bool value) async {
    final map = Map<int, bool>.from(AppPreferences.personEnabled);
    map[personId] = value;
    await AppPreferences.setPersonEnabled(map);
    state = PersonsState(persons: state.persons);
  }

  Future<void> setColor(int personId, String hex) async {
    final map = Map<int, String>.from(AppPreferences.personColors);
    map[personId] = hex;
    await AppPreferences.setPersonColors(map);
    // Rebuild person list with updated color
    final h = hex.replaceFirst('#', '');
    final c = Color(int.parse('FF$h', radix: 16));
    final updated = state.persons.map((p) {
      if (p.id == personId) {
        return Person(id: p.id, name: p.name, isMe: p.isMe, color: c, canManageAgenda: p.canManageAgenda);
      }
      return p;
    }).toList();
    state = PersonsState(persons: updated);
  }
}

final personsProvider =
    NotifierProvider<PersonsNotifier, PersonsState>(PersonsNotifier.new);
