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
      final persons = raw
          .map((e) => Person.fromJson(e as Map<String, dynamic>))
          .toList();
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
}

final personsProvider =
    NotifierProvider<PersonsNotifier, PersonsState>(PersonsNotifier.new);
