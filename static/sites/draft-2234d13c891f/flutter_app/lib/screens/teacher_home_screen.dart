import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';
import '../services/ble_service.dart';
import '../models/models.dart';
import 'login_screen.dart';

class TeacherHomeScreen extends StatefulWidget {
  const TeacherHomeScreen({super.key});
  @override
  State<TeacherHomeScreen> createState() => _TeacherHomeScreenState();
}

class _TeacherHomeScreenState extends State<TeacherHomeScreen> {
  SessionModel? _session;
  String? _currentToken;
  DateTime? _tokenExpiry;
  List<Map<String, dynamic>> _attendance = [];
  Map<String, dynamic>? _report;
  Timer? _tokenTimer, _sessionTimer, _attendanceTimer;
  int _tokenSecondsLeft = 15;
  bool _loading = false;
  final _subjectCtrl = TextEditingController(text: 'Data Structures');
  final _classCtrl   = TextEditingController(text: 'CS-3A');
  int _windowMin = 5, _rssiThreshold = -65;

  @override
  void dispose() {
    _tokenTimer?.cancel(); _sessionTimer?.cancel(); _attendanceTimer?.cancel();
    _subjectCtrl.dispose(); _classCtrl.dispose();
    BleService.stopAdvertising();
    super.dispose();
  }

  Future<void> _startSession() async {
    setState(() => _loading = true);
    final token = context.read<AuthProvider>().user!.token;
    try {
      final res = await ApiService.startSession(
        subject: _subjectCtrl.text, className: _classCtrl.text,
        windowMinutes: _windowMin, rssiThreshold: _rssiThreshold, token: token,
      );
      if (res['success'] == true) {
        final session = SessionModel.fromJson(res['session']);
        final tok = res['token']['value'] as String;
        setState(() {
          _session = session; _currentToken = tok;
          _tokenExpiry = DateTime.parse(res['token']['expires_at']);
          _tokenSecondsLeft = 15;
        });
        await BleService.startAdvertising(session.sessionId, tok);
        _startTimers();
        _snack('Session started!', Colors.green);
      } else {
        _snack(res['message'] ?? 'Failed', Colors.red);
      }
    } catch (e) { _snack('Error: $e', Colors.red); }
    setState(() => _loading = false);
  }

  Future<void> _stopSession() async {
    if (_session == null) return;
    final token = context.read<AuthProvider>().user!.token;
    final res = await ApiService.stopSession(_session!.sessionId, token);
    if (res['success'] == true) {
      _tokenTimer?.cancel(); _sessionTimer?.cancel(); _attendanceTimer?.cancel();
      await BleService.stopAdvertising();
      await _loadReport();
      setState(() { _session = null; _currentToken = null; });
      _snack('Session ended', Colors.blueGrey);
    }
  }

  void _startTimers() {
    _tokenTimer = Timer.periodic(const Duration(seconds: 1), (_) async {
      final left = _tokenExpiry!.difference(DateTime.now()).inSeconds;
      setState(() => _tokenSecondsLeft = left.clamp(0, 15));
      if (left <= 1) {
        final token = context.read<AuthProvider>().user!.token;
        final res = await ApiService.getSessionToken(_session!.sessionId, token);
        if (res['success'] == true) {
          final newTok = res['token'] as String;
          setState(() {
            _currentToken = newTok;
            _tokenExpiry = DateTime.parse(res['expires_at']);
            _tokenSecondsLeft = 15;
          });
          await BleService.updateToken(_session!.sessionId, newTok);
        }
      }
    });
    _sessionTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (_session != null && _session!.isExpired) _stopSession();
      else setState(() {});
    });
    _attendanceTimer = Timer.periodic(const Duration(seconds: 5), (_) => _refreshAttendance());
  }

  Future<void> _refreshAttendance() async {
    if (_session == null) return;
    final token = context.read<AuthProvider>().user!.token;
    try {
      final res = await ApiService.getSessionAttendance(_session!.sessionId, token);
      if (res['success'] == true)
        setState(() => _attendance = List<Map<String, dynamic>>.from(res['attendance']));
    } catch (_) {}
  }

  Future<void> _loadReport() async {
    if (_session == null) return;
    final token = context.read<AuthProvider>().user!.token;
    try {
      final res = await ApiService.getAttendanceReport(_session!.sessionId, token);
      if (res['success'] == true) setState(() => _report = res);
    } catch (_) {}
  }

  void _snack(String msg, Color color) => ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(msg), backgroundColor: color, behavior: SnackBarBehavior.floating));

  @override
  Widget build(BuildContext context) {
    final user = context.read<AuthProvider>().user!;
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1565C0),
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Teacher Dashboard', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          Text(user.name, style: const TextStyle(color: Color(0xFFBBDEFB), fontSize: 12)),
        ]),
        actions: [IconButton(
          icon: const Icon(Icons.logout, color: Colors.white),
          onPressed: () async {
            await context.read<AuthProvider>().logout();
            if (mounted) Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
          },
        )],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: _session == null ? _buildSetup() : _buildLiveSession(),
      ),
    );
  }

  Widget _buildSetup() => Column(children: [
    _card('Start Attendance Session', Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _label('Subject'),
      TextField(controller: _subjectCtrl, decoration: _inputDecor('e.g. Data Structures')),
      const SizedBox(height: 12),
      _label('Class'),
      TextField(controller: _classCtrl, decoration: _inputDecor('e.g. CS-3A')),
      const SizedBox(height: 12),
      _label('Window: $_windowMin min'),
      Slider(value: _windowMin.toDouble(), min: 1, max: 15, divisions: 14,
        activeColor: const Color(0xFF1565C0),
        onChanged: (v) => setState(() => _windowMin = v.round())),
      _label('Min RSSI: $_rssiThreshold dBm'),
      Slider(value: _rssiThreshold.toDouble(), min: -90, max: -40, divisions: 50,
        activeColor: const Color(0xFF1565C0),
        onChanged: (v) => setState(() => _rssiThreshold = v.round())),
      const SizedBox(height: 12),
      SizedBox(width: double.infinity, height: 48,
        child: ElevatedButton.icon(
          onPressed: _loading ? null : _startSession,
          icon: _loading
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Icon(Icons.play_arrow),
          label: const Text('Start Session', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        )),
    ])),
    if (_report != null) _buildReport(),
  ]);

  Widget _buildLiveSession() {
    final left = _session!.timeLeft;
    final totalSecs = _session!.windowMinutes * 60;
    final leftSecs = left.inSeconds.clamp(0, totalSecs);
    return Column(children: [
      Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: const LinearGradient(colors: [Color(0xFF1565C0), Color(0xFF0D47A1)]),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(children: [
          Text('${_session!.subject} · ${_session!.className}',
              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 16),
          const Text('Current Token', style: TextStyle(color: Color(0xFFBBDEFB), fontSize: 12)),
          const SizedBox(height: 4),
          Text(_currentToken ?? '——',
              style: const TextStyle(color: Colors.white, fontSize: 38, fontWeight: FontWeight.bold, letterSpacing: 10)),
          const SizedBox(height: 12),
          LinearProgressIndicator(value: _tokenSecondsLeft / 15,
              backgroundColor: Colors.white24, valueColor: const AlwaysStoppedAnimation(Colors.white)),
          const SizedBox(height: 4),
          Text('Rotates in ${_tokenSecondsLeft}s', style: const TextStyle(color: Color(0xFFBBDEFB), fontSize: 12)),
          const SizedBox(height: 12),
          LinearProgressIndicator(value: leftSecs / totalSecs,
              backgroundColor: Colors.white24, valueColor: const AlwaysStoppedAnimation(Color(0xFF81C784))),
          const SizedBox(height: 4),
          Text('${left.inMinutes}m ${left.inSeconds % 60}s remaining',
              style: const TextStyle(color: Color(0xFFBBDEFB), fontSize: 12)),
        ]),
      ),
      const SizedBox(height: 12),
      Row(children: [
        _stat('Present', '${_attendance.length}', const Color(0xFF2E7D32)),
        const SizedBox(width: 10),
        _stat('RSSI Min', '${_session!.rssiThreshold}', const Color(0xFF1565C0)),
        const SizedBox(width: 10),
        _stat('Window', '${_session!.windowMinutes}m', const Color(0xFFF57F17)),
      ]),
      const SizedBox(height: 12),
      _card('Attendance (${_attendance.length})', _attendance.isEmpty
          ? const Padding(padding: EdgeInsets.symmetric(vertical: 16),
              child: Center(child: Text('Waiting for students...', style: TextStyle(color: Colors.grey))))
          : Column(children: _attendance.map((a) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(backgroundColor: const Color(0xFFE8F5E9),
                child: Text((a['name'] as String)[0], style: const TextStyle(color: Color(0xFF2E7D32), fontWeight: FontWeight.bold))),
              title: Text(a['name'], style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
              subtitle: Text('${a['roll_number']} · RSSI: ${a['rssi_value']} dBm',
                  style: const TextStyle(fontSize: 12, color: Colors.grey)),
              trailing: const Icon(Icons.check_circle, color: Color(0xFF2E7D32)),
            )).toList())),
      const SizedBox(height: 8),
      SizedBox(width: double.infinity, height: 48,
        child: OutlinedButton.icon(
          onPressed: _stopSession,
          icon: const Icon(Icons.stop, color: Color(0xFFC62828)),
          label: const Text('Stop Session', style: TextStyle(color: Color(0xFFC62828), fontWeight: FontWeight.w600)),
          style: OutlinedButton.styleFrom(side: const BorderSide(color: Color(0xFFC62828)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        )),
    ]);
  }

  Widget _buildReport() {
    final absent = List.from(_report!['absent'] ?? []);
    final present = List.from(_report!['present'] ?? []);
    return _card('Last Session Report', Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Present: ${present.length}  |  Absent: ${absent.length}', style: const TextStyle(fontWeight: FontWeight.w600)),
      const SizedBox(height: 8),
      if (absent.isNotEmpty) ...[
        const Text('Absent:', style: TextStyle(color: Color(0xFFC62828), fontWeight: FontWeight.w600, fontSize: 13)),
        ...absent.map((s) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 2),
          child: Row(children: [
            const Icon(Icons.cancel_outlined, color: Color(0xFFC62828), size: 16),
            const SizedBox(width: 6),
            Text('${s['name']} (${s['roll_number']})', style: const TextStyle(fontSize: 13)),
          ]),
        )),
      ],
    ]));
  }

  Widget _card(String title, Widget child) => Container(
    width: double.infinity, margin: const EdgeInsets.only(bottom: 14),
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE8E8E8))),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
      const SizedBox(height: 12), child,
    ]),
  );

  Widget _stat(String label, String value, Color color) => Expanded(child: Container(
    padding: const EdgeInsets.symmetric(vertical: 12),
    decoration: BoxDecoration(color: color.withOpacity(0.08), borderRadius: BorderRadius.circular(10)),
    child: Column(children: [
      Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
      Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
    ]),
  ));

  Widget _label(String t) => Padding(padding: const EdgeInsets.only(bottom: 4),
    child: Text(t, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Color(0xFF444444))));

  InputDecoration _inputDecor(String hint) => InputDecoration(
    hintText: hint, hintStyle: const TextStyle(color: Color(0xFFAAAAAA)),
    filled: true, fillColor: const Color(0xFFF5F5F5),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
  );
}
