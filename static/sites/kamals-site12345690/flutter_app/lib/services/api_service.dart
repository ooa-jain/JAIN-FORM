import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();

  static Future<String?> getToken() => _storage.read(key: 'jwt');
  static Future<void> saveToken(String t) => _storage.write(key: 'jwt', value: t);
  static Future<void> clearToken() => _storage.delete(key: 'jwt');

  static Map<String, String> _headers([String? token]) => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  static Future<Map<String, dynamic>> _post(String path, Map body, {String? token}) async {
    final res = await http.post(
      Uri.parse('${AppConfig.baseUrl}$path'),
      headers: _headers(token),
      body: jsonEncode(body),
    ).timeout(Duration(seconds: AppConfig.apiTimeoutSecs));
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> _get(String path, {String? token}) async {
    final res = await http.get(
      Uri.parse('${AppConfig.baseUrl}$path'),
      headers: _headers(token),
    ).timeout(Duration(seconds: AppConfig.apiTimeoutSecs));
    return jsonDecode(res.body);
  }

  // Auth
  static Future<Map<String, dynamic>> login(String email, String password, String role) =>
      _post('/auth/login', {'email': email, 'password': password, 'role': role});

  static Future<Map<String, dynamic>> registerDevice(String studentId, String deviceId, String token) =>
      _post('/auth/register-device', {'student_id': studentId, 'device_id': deviceId}, token: token);

  // Sessions
  static Future<Map<String, dynamic>> startSession({
    required String subject, required String className,
    required int windowMinutes, required int rssiThreshold, required String token,
  }) => _post('/sessions/start', {
    'subject': subject, 'class_name': className,
    'window_minutes': windowMinutes, 'rssi_threshold': rssiThreshold,
  }, token: token);

  static Future<Map<String, dynamic>> stopSession(String sessionId, String token) async {
    final res = await http.post(
      Uri.parse('${AppConfig.baseUrl}/sessions/$sessionId/stop'),
      headers: _headers(token),
    ).timeout(Duration(seconds: AppConfig.apiTimeoutSecs));
    return jsonDecode(res.body);
  }

  static Future<Map<String, dynamic>> getSessionToken(String sessionId, String token) =>
      _get('/sessions/$sessionId/token', token: token);

  static Future<Map<String, dynamic>> getSessionAttendance(String sessionId, String token) =>
      _get('/sessions/$sessionId/attendance', token: token);

  static Future<Map<String, dynamic>> getAttendanceReport(String sessionId, String token) =>
      _get('/attendance/report/$sessionId', token: token);

  static Future<Map<String, dynamic>> checkActiveSession(String token) =>
      _get('/sessions/active', token: token);

  static Future<Map<String, dynamic>> markAttendance({
    required String sessionId, required String token,
    required int rssi, required String deviceId, required String jwtToken,
  }) => _post('/attendance/mark', {
    'session_id': sessionId, 'token': token, 'rssi': rssi, 'device_id': deviceId,
  }, token: jwtToken);

  static Future<Map<String, dynamic>> getMyAttendance(String token) =>
      _get('/attendance/my', token: token);
}
