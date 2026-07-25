import 'package:dio/dio.dart';
import 'auth_exception.dart';

bool isAuthError(Object err) =>
    err is AuthRequiredException ||
    err.toString().contains('AuthRequiredException');

bool isNetworkError(Object err) {
  if (isAuthError(err)) return false;
  if (err is DioException) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError ||
        (err.type == DioExceptionType.unknown && err.response == null);
  }
  return false;
}

/// User-facing message for connectivity/DNS failures (e.g. after screen wake).
String friendlyErrorMessage(Object err) {
  if (isAuthError(err)) {
    return 'Sessie verlopen. Log opnieuw in.';
  }
  if (isNetworkError(err)) {
    return 'Geen verbinding met de server. Controleer je netwerk en probeer opnieuw.';
  }
  if (err is DioException) {
    final detail = err.response?.data;
    if (detail is Map && detail['detail'] != null) {
      return detail['detail'].toString();
    }
    if (err.message != null && err.message!.isNotEmpty) {
      return err.message!;
    }
  }
  return err.toString();
}
