import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import '../config.dart';
import '../models/models.dart';

class BleService {
  static const _channel = MethodChannel('com.attendance/ble');
  static StreamSubscription? _scanSub;

  // TEACHER — start BLE broadcast (calls native Android)
  static Future<bool> startAdvertising(String sessionId, String token) async {
    try {
      final result = await _channel.invokeMethod<bool>('startAdvertising',
          {'sessionId': sessionId, 'token': token});
      return result ?? false;
    } on PlatformException catch (e) {
      print('[BLE] Advertise error: ${e.message}');
      return false;
    }
  }

  static Future<void> stopAdvertising() async {
    try { await _channel.invokeMethod('stopAdvertising'); } catch (_) {}
  }

  static Future<void> updateToken(String sessionId, String token) async {
    try {
      await _channel.invokeMethod('updateToken', {'sessionId': sessionId, 'token': token});
    } catch (_) {}
  }

  // STUDENT — scan for teacher's BLE device
  static Future<BleTeacherDevice?> scanForTeacher({
    Duration timeout = const Duration(seconds: 10),
    void Function(int rssi)? onSignalUpdate,
  }) async {
    final state = await FlutterBluePlus.adapterState.first;
    if (state != BluetoothAdapterState.on) {
      throw Exception('Bluetooth is off. Please enable Bluetooth.');
    }

    BleTeacherDevice? found;
    final completer = Completer<BleTeacherDevice?>();

    await FlutterBluePlus.startScan(timeout: timeout);

    _scanSub = FlutterBluePlus.scanResults.listen((results) {
      for (final r in results) {
        final name = r.device.platformName;
        final uuids = r.advertisementData.serviceUuids
            .map((u) => u.toString().toLowerCase()).toList();
        final isTeacher = name == AppConfig.bleDeviceName ||
            name.startsWith('ATT_') ||
            uuids.contains(AppConfig.bleServiceUuid.toLowerCase());

        if (isTeacher) {
          onSignalUpdate?.call(r.rssi);
          String? sessionId, token;
          try {
            final mfgData = r.advertisementData.manufacturerData;
            if (mfgData.isNotEmpty) {
              final bytes = mfgData.values.first;
              final decoded = utf8.decode(bytes);
              final parts = decoded.split('|');
              if (parts.length >= 2) { sessionId = parts[0]; token = parts[1]; }
            }
          } catch (_) {}

          found = BleTeacherDevice(
            deviceId: r.device.remoteId.str,
            rssi: r.rssi, sessionId: sessionId, token: token,
          );
          if (!completer.isCompleted) completer.complete(found);
        }
      }
    });

    Future.delayed(timeout, () {
      if (!completer.isCompleted) completer.complete(null);
    });

    await FlutterBluePlus.stopScan();
    _scanSub?.cancel();
    return completer.future;
  }

  static String rssiToQuality(int rssi) {
    if (rssi >= -50) return 'Excellent';
    if (rssi >= -60) return 'Good';
    if (rssi >= -70) return 'Fair';
    if (rssi >= -80) return 'Weak';
    return 'Very Weak';
  }

  static int rssiToBars(int rssi) {
    if (rssi >= -50) return 5;
    if (rssi >= -60) return 4;
    if (rssi >= -70) return 3;
    if (rssi >= -80) return 2;
    return 1;
  }

  static void dispose() => _scanSub?.cancel();
}
