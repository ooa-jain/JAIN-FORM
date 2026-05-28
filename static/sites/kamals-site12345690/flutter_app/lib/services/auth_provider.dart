import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/models.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  UserModel? _user;
  bool _loading = false;
  String? _error;

  UserModel? get user => _user;
  bool get loading => _loading;
  String? get error => _error;
  bool get isLoggedIn => _user != null;

  Future<void> tryRestoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final userJson = prefs.getString('user');
    if (userJson != null) {
      try {
        final map = jsonDecode(userJson);
        _user = UserModel.fromJson({'user': map}, map['token']);
        notifyListeners();
      } catch (_) {
        await prefs.remove('user');
      }
    }
  }

  Future<bool> login(String email, String password, String role) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final result = await ApiService.login(email, password, role);
      if (result['success'] == true) {
        final token = result['token'];
        _user = UserModel.fromJson(result, token);
        await ApiService.saveToken(token);
        final prefs = await SharedPreferences.getInstance();
        final userMap = {...(result['user'] as Map<String, dynamic>), 'token': token};
        await prefs.setString('user', jsonEncode(userMap));
        _loading = false;
        notifyListeners();
        return true;
      } else {
        _error = result['message'] ?? 'Login failed';
        _loading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Cannot connect to server. Check your WiFi and server IP in config.dart';
      _loading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _user = null;
    await ApiService.clearToken();
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user');
    notifyListeners();
  }
}
