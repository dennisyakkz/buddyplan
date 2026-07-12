import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/preferences.dart';
import '../data/dashboard_repository.dart';

class AuthState {
  final bool isLoggedIn;
  final String? name;
  final bool isLoading;
  final String? error;
  final bool sessionExpired;

  const AuthState({
    required this.isLoggedIn,
    this.name,
    this.isLoading = false,
    this.error,
    this.sessionExpired = false,
  });
}

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    final token = AppPreferences.authToken;
    return AuthState(
      isLoggedIn: token != null && token.isNotEmpty,
      name: AppPreferences.loggedInName,
    );
  }

  Future<bool> login(String url, String username, String password) async {
    state = AuthState(isLoggedIn: false, isLoading: true);
    try {
      await AppPreferences.setServerUrl(url);
      ApiClient.instance.reset();
      final result = await ApiClient.instance.login(username, password);
      await AppPreferences.setAuthToken(result['token'] as String);
      await AppPreferences.setLoggedInName(result['name'] as String);
      ApiClient.instance.reset();
      state = AuthState(isLoggedIn: true, name: result['name'] as String);
      return true;
    } catch (e) {
      state = AuthState(
          isLoggedIn: false, error: 'Inloggen mislukt. Controleer URL en gegevens.');
      return false;
    }
  }

  void handleSessionExpired() {
    if (state.sessionExpired) return;
    AppPreferences.setAuthToken(null);
    ApiClient.instance.reset();
    state = AuthState(
      isLoggedIn: true,
      name: state.name,
      sessionExpired: true,
    );
  }

  Future<void> dismissSessionExpired() async {
    await AppPreferences.setLoggedInName(null);
    await DashboardRepository.reset();
    DashboardRepository.close();
    state = const AuthState(isLoggedIn: false);
  }

  Future<void> logout() async {
    await AppPreferences.setAuthToken(null);
    await AppPreferences.setLoggedInName(null);
    await DashboardRepository.reset();
    DashboardRepository.close();
    ApiClient.instance.reset();
    state = const AuthState(isLoggedIn: false);
  }
}

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);
