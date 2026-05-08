import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';
import '../services/ble_service.dart';
import '../services/device_service.dart';
import '../models/models.dart';
import 'login_screen.dart';

enum ScanState { idle, scanning, found, notFound }
enum MarkState { idle, marking, success, failed }

class StudentHomeScreen extends StatefulWidget {
  const StudentHomeScreen({super.key});
  @override
  State<StudentHomeScreen> createState() => _StudentHomeScreenState();
}

class _StudentHomeScreenState extends State<StudentHomeScreen>
    with SingleTickerProviderStateMixin {
  ScanState _scan = ScanState.idle;
  MarkState _mark = MarkState.idle;
  BleTeacherDevice? _device;
  SessionModel? _session;
  List<AttendanceRecord> _history = [];
  String? _errorMsg, _successMsg;
  int _tab = 0;
  late AnimationController _pulse;
  late Animation<double> _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(vsync: this, duration: const Duration(seconds: 1))
      ..repeat(reverse: true);
    _pulseAnim = Tween<double>(begin: 0.95, end: 1.05).animate(
        CurvedAnimation(parent: _pulse, curve: Curves.easeInOut));
    _loadHistory();
  }

  @override
  void dispose() { _pulse.dispose(); BleService.dispose(); super.dispose(); }

  Future<void> _loadHistory() async {
    final token = context.read<AuthProvider>().user!.token;
    try {
      final res = await ApiService.getMyAttendance(token);
      if (res['success'] == true) {
        setState(() => _history = (res['records'] as List)
            .map((r) => AttendanceRecord.fromJson(r)).toList());
      }
    } catch (_) {}
  }

  Future<void> _scanBle() async {
    setState(() { _scan = ScanState.scanning; _errorMsg = null; _device = null; });
    final token = context.read<AuthProvider>().user!.token;
    try {
      final sessionRes = await ApiService.checkActiveSession(token);
      if (sessionRes['active'] != true) {
        setState(() { _scan = ScanState.notFound; _errorMsg = 'No active session. Ask teacher to start one.'; });
        return;
      }
      _session = SessionModel.fromJson(sessionRes['session']);
    } catch (e) {
      setState(() { _scan = ScanState.notFound; _errorMsg = 'Cannot reach server. Check network.'; });
      return;
    }

    try {
      final device = await BleService.scanForTeacher(
        timeout: const Duration(seconds: 8),
        onSignalUpdate: (rssi) => setState(() {}),
      );
      if (device != null) {
        setState(() { _scan = ScanState.found; _device = device; });
      } else {
        setState(() { _scan = ScanState.notFound; _errorMsg = 'Teacher device not found. Make sure Bluetooth is on and you are nearby.'; });
      }
    } catch (e) {
      setState(() { _scan = ScanState.notFound; _errorMsg = e.toString(); });
    }
  }

  Future<void> _markAttendance() async {
    if (_device == null || _session == null) return;
    setState(() { _mark = MarkState.marking; _errorMsg = null; });

    final user = context.read<AuthProvider>().user!;
    final deviceId = await DeviceService.getDeviceId();
    final bleToken = _device!.token;

    if (bleToken == null || bleToken.isEmpty) {
      setState(() { _mark = MarkState.failed; _errorMsg = 'Could not read token from BLE signal.'; });
      return;
    }

    try {
      final res = await ApiService.markAttendance(
        sessionId: _session!.sessionId, token: bleToken,
        rssi: _device!.rssi, deviceId: deviceId, jwtToken: user.token,
      );
      if (res['success'] == true) {
        setState(() {
          _mark = MarkState.success;
          _successMsg = 'Marked at ${TimeOfDay.now().format(context)}';
        });
        await _loadHistory();
      } else {
        setState(() { _mark = MarkState.failed; _errorMsg = res['message'] ?? 'Failed'; });
      }
    } catch (e) {
      setState(() { _mark = MarkState.failed; _errorMsg = 'Network error: $e'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.read<AuthProvider>().user!;
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1565C0),
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Mark Attendance', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          Text(user.name, style: const TextStyle(color: Color(0xFFBBDEFB), fontSize: 12)),
        ]),
        actions: [IconButton(
          icon: const Icon(Icons.logout, color: Colors.white),
          onPressed: () async {
            await context.read<AuthProvider>().logout();
            if (mounted) Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
          },
        )],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(42),
          child: Row(children: [
            _tabBtn('Mark Attendance', 0),
            _tabBtn('My History', 1),
          ]),
        ),
      ),
      body: _tab == 0 ? _buildMarkTab() : _buildHistoryTab(),
    );
  }

  Widget _buildMarkTab() => SingleChildScrollView(
    padding: const EdgeInsets.all(16),
    child: Column(children: [
      if (_mark == MarkState.success) _successCard()
      else _scanCard(),
      if (_mark != MarkState.success) _deviceInfoCard(),
    ]),
  );

  Widget _scanCard() => Container(
    padding: const EdgeInsets.all(24),
    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE0E0E0))),
    child: Column(children: [
      ScaleTransition(
        scale: _scan == ScanState.scanning ? _pulseAnim : const AlwaysStoppedAnimation(1.0),
        child: Container(width: 90, height: 90,
          decoration: BoxDecoration(color: _scanColor().withOpacity(0.12), shape: BoxShape.circle),
          child: Icon(_scanIcon(), size: 44, color: _scanColor())),
      ),
      const SizedBox(height: 16),
      Text(_scanLabel(), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 6),
      Text(_scanSub(), textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 13, color: Colors.grey)),

      if (_mark == MarkState.failed && _errorMsg != null) ...[
        const SizedBox(height: 12),
        Container(padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: const Color(0xFFFFEBEE), borderRadius: BorderRadius.circular(8)),
          child: Row(children: [
            const Icon(Icons.warning_amber, color: Color(0xFFC62828), size: 16),
            const SizedBox(width: 8),
            Expanded(child: Text(_errorMsg!, style: const TextStyle(fontSize: 12, color: Color(0xFFC62828)))),
          ])),
      ],

      if (_scan == ScanState.notFound && _errorMsg != null && _mark != MarkState.failed) ...[
        const SizedBox(height: 12),
        Container(padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: const Color(0xFFFFEBEE), borderRadius: BorderRadius.circular(8)),
          child: Text(_errorMsg!, style: const TextStyle(fontSize: 12, color: Color(0xFFC62828)))),
      ],

      const SizedBox(height: 20),
      if (_scan != ScanState.found)
        SizedBox(width: double.infinity, height: 48,
          child: ElevatedButton.icon(
            onPressed: _scan == ScanState.scanning ? null : _scanBle,
            icon: _scan == ScanState.scanning
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.bluetooth_searching),
            label: Text(_scan == ScanState.scanning ? 'Scanning...' : 'Scan for Teacher',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1565C0), foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          )),

      if (_scan == ScanState.found && _device != null) ...[
        const SizedBox(height: 16),
        _signalBars(_device!.rssi),
        const SizedBox(height: 16),
        SizedBox(width: double.infinity, height: 48,
          child: ElevatedButton.icon(
            onPressed: _mark == MarkState.marking ? null : _markAttendance,
            icon: _mark == MarkState.marking
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.check_circle),
            label: Text(_mark == MarkState.marking ? 'Marking...' : 'Mark My Attendance',
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          )),
      ],
    ]),
  );

  Widget _successCard() => Container(
    padding: const EdgeInsets.all(28),
    decoration: BoxDecoration(color: const Color(0xFFF1F8E9), borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF81C784))),
    child: Column(children: [
      const Icon(Icons.check_circle, color: Color(0xFF2E7D32), size: 72),
      const SizedBox(height: 12),
      const Text('Attendance Marked!',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
      const SizedBox(height: 6),
      Text(_successMsg ?? '', style: const TextStyle(color: Color(0xFF388E3C))),
      const SizedBox(height: 20),
      TextButton(
        onPressed: () => setState(() { _mark = MarkState.idle; _scan = ScanState.idle; }),
        child: const Text('Mark for Another Session'),
      ),
    ]),
  );

  Widget _deviceInfoCard() => FutureBuilder<String>(
    future: DeviceService.getDeviceId(),
    builder: (_, snap) => Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE0E0E0))),
      child: Row(children: [
        const Icon(Icons.phone_android, color: Color(0xFF1565C0)),
        const SizedBox(width: 10),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Your Device ID', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          Text(snap.data ?? '...', style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ])),
        const Icon(Icons.verified, color: Color(0xFF2E7D32)),
      ]),
    ),
  );

  Widget _signalBars(int rssi) {
    final bars = BleService.rssiToBars(rssi);
    return Row(mainAxisAlignment: MainAxisAlignment.center, children: [
      ...List.generate(5, (i) => Container(
        width: 10, height: 10 + i * 6.0, margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          color: i < bars ? const Color(0xFF1565C0) : const Color(0xFFE0E0E0),
          borderRadius: BorderRadius.circular(2),
        ),
      )),
      const SizedBox(width: 10),
      Text('$rssi dBm · ${BleService.rssiToQuality(rssi)}',
          style: const TextStyle(fontSize: 13, color: Color(0xFF444444))),
    ]);
  }

  Widget _buildHistoryTab() {
    if (_history.isEmpty) return const Center(
        child: Text('No records yet.', style: TextStyle(color: Colors.grey)));
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (_, i) {
        final r = _history[i];
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE8E8E8))),
          child: Row(children: [
            Container(width: 42, height: 42,
              decoration: BoxDecoration(color: const Color(0xFFE8F5E9), borderRadius: BorderRadius.circular(8)),
              child: const Icon(Icons.check, color: Color(0xFF2E7D32))),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(r.subject, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
              Text('${r.className} · ${r.teacherName ?? ""}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey)),
              Text('${r.timestamp.day}/${r.timestamp.month}/${r.timestamp.year} '
                  '${r.timestamp.hour}:${r.timestamp.minute.toString().padLeft(2, '0')}',
                  style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ])),
            Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: const Color(0xFFE8F5E9), borderRadius: BorderRadius.circular(6)),
              child: const Text('Present', style: TextStyle(color: Color(0xFF2E7D32), fontSize: 12, fontWeight: FontWeight.w600))),
          ]),
        );
      },
    );
  }

  Color _scanColor() {
    switch (_scan) {
      case ScanState.scanning: return const Color(0xFF1565C0);
      case ScanState.found:    return const Color(0xFF2E7D32);
      case ScanState.notFound: return const Color(0xFFC62828);
      default:                 return const Color(0xFF666666);
    }
  }
  IconData _scanIcon() {
    switch (_scan) {
      case ScanState.scanning: return Icons.bluetooth_searching;
      case ScanState.found:    return Icons.bluetooth_connected;
      case ScanState.notFound: return Icons.bluetooth_disabled;
      default:                 return Icons.bluetooth;
    }
  }
  String _scanLabel() {
    switch (_scan) {
      case ScanState.scanning: return 'Scanning...';
      case ScanState.found:    return 'Teacher Found!';
      case ScanState.notFound: return 'Not Found';
      default:                 return 'Ready to Scan';
    }
  }
  String _scanSub() {
    switch (_scan) {
      case ScanState.scanning: return 'Looking for teacher\'s BLE device nearby';
      case ScanState.found:    return 'Tap button below to mark your attendance';
      case ScanState.notFound: return 'Could not detect teacher\'s device nearby';
      default:                 return 'Press Scan to detect teacher\'s BLE signal';
    }
  }
  Widget _tabBtn(String label, int idx) => Expanded(child: GestureDetector(
    onTap: () => setState(() => _tab = idx),
    child: Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(border: Border(bottom: BorderSide(
          color: _tab == idx ? Colors.white : Colors.transparent, width: 2))),
      child: Text(label, textAlign: TextAlign.center,
          style: TextStyle(color: _tab == idx ? Colors.white : const Color(0xFF90CAF9),
              fontWeight: _tab == idx ? FontWeight.w600 : FontWeight.normal, fontSize: 13)),
    ),
  ));
}
