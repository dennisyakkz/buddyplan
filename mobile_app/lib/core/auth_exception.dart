class AuthRequiredException implements Exception {
  const AuthRequiredException();
  @override
  String toString() => 'Niet ingelogd of token verlopen';
}
