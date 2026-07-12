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
  return true;
}
