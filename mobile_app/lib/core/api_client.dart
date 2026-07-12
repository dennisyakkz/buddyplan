import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'auth_exception.dart';
import 'preferences.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  Dio? _dio;

  Dio get dio {
    _dio ??= _buildDio();
    return _dio!;
  }

  Dio _buildDio() {
    final d = Dio(BaseOptions(
      baseUrl: AppPreferences.serverUrl.isEmpty
          ? (kDebugMode ? 'http://localhost:8000' : '')
          : AppPreferences.serverUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      contentType: 'application/json',
    ));

    d.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = AppPreferences.authToken;
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          handler.reject(
            DioException(
              requestOptions: error.requestOptions,
              error: const AuthRequiredException(),
              type: DioExceptionType.badResponse,
              response: error.response,
            ),
          );
          return;
        }
        handler.next(error);
      },
    ));

    return d;
  }

  /// Call after URL or token change.
  void reset() => _dio = null;

  // ------------------------------------------------------------------
  // Auth
  // ------------------------------------------------------------------

  Future<Map<String, dynamic>> login(String username, String password) async {
    final deviceName = Platform.isAndroid
        ? 'Android ${Platform.operatingSystemVersion}'
        : Platform.isIOS
            ? 'iOS ${Platform.operatingSystemVersion}'
            : 'Mobiel';
    final resp = await dio.post('/api/auth/login', data: {
      'username': username,
      'password': password,
      'device_id': AppPreferences.deviceId,
      'device_name': deviceName,
      'device_type': 'mobile',
    });
    return resp.data as Map<String, dynamic>;
  }

  // ------------------------------------------------------------------
  // Mobile endpoints
  // ------------------------------------------------------------------

  Future<List<dynamic>> fetchPersons() async {
    final resp = await dio.get('/api/mobile/persons');
    return resp.data as List<dynamic>;
  }

  Future<List<dynamic>> fetchCalendar(String start, String end) async {
    final resp = await dio.get('/api/mobile/calendar',
        queryParameters: {'start': start, 'end': end});
    return resp.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> fetchCalendarEventDetail(int id) async {
    final resp = await dio.get('/api/mobile/calendar/$id');
    return resp.data as Map<String, dynamic>;
  }

  Future<List<dynamic>> fetchTasks(String start, String end,
      {int? personId}) async {
    final params = <String, dynamic>{'start': start, 'end': end};
    if (personId != null) params['person_id'] = personId;
    final resp = await dio.get('/api/mobile/tasks', queryParameters: params);
    return resp.data as List<dynamic>;
  }

  // ------------------------------------------------------------------
  // Agenda CRUD
  // ------------------------------------------------------------------

  Future<Map<String, dynamic>> createCalendarEvent(
      Map<String, dynamic> data) async {
    final resp = await dio.post('/api/agenda', data: data);
    return resp.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateCalendarEvent(
      int id, Map<String, dynamic> data) async {
    final resp = await dio.put('/api/agenda/$id', data: data);
    return resp.data as Map<String, dynamic>;
  }

  Future<void> deleteCalendarEvent(int id) async {
    await dio.delete('/api/agenda/$id');
  }

  // ------------------------------------------------------------------
  // Tasks CRUD
  // ------------------------------------------------------------------

  Future<Map<String, dynamic>> createTask(
      int personId, Map<String, dynamic> data) async {
    final resp = await dio
        .post('/api/tasks', data: data, queryParameters: {'person_id': personId});
    return resp.data as Map<String, dynamic>;
  }

  Future<void> completeTask(String taskId, String date) async {
    await dio.post('/api/tasks/$taskId/complete',
        queryParameters: {'date': date});
  }

  Future<Map<String, dynamic>> fetchTaskDetail(int taskId) async {
    final resp = await dio.get('/api/tasks/$taskId');
    return resp.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateTask(
      int id, Map<String, dynamic> data) async {
    final resp = await dio.put('/api/tasks/$id', data: data);
    return resp.data as Map<String, dynamic>;
  }

  Future<void> deleteTask(int id) async {
    await dio.delete('/api/tasks/$id');
  }

  // ------------------------------------------------------------------
  // Persons list (for task assignment)
  // ------------------------------------------------------------------

  Future<List<dynamic>> fetchAppUsers() async {
    final resp = await dio.get('/api/app/users');
    return resp.data as List<dynamic>;
  }
}
