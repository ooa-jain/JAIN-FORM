import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';

class DeviceService {
  static String? _cachedId;

  static Future<String> getDeviceId() async {
    if (_cachedId != null) return _cachedId!;
    final info = DeviceInfoPlugin();
    try {
      if (defaultTargetPlatform == TargetPlatform.android) {
        final android = await info.androidInfo;
        _cachedId = 'AND-${android.id}';
      } else if (defaultTargetPlatform == TargetPlatform.iOS) {
        final ios = await info.iosInfo;
        _cachedId = 'IOS-${ios.identifierForVendor ?? 'unknown'}';
      } else {
        _cachedId = 'DEV-UNKNOWN';
      }
    } catch (e) {
      _cachedId = 'DEV-${DateTime.now().millisecondsSinceEpoch}';
    }
    return _cachedId!;
  }
}
