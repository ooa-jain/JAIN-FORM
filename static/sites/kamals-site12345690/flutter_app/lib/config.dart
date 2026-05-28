class AppConfig {
  // ── IMPORTANT: Change this to your PC's IP address ──
  // Step 1: Open cmd → type "ipconfig" → find IPv4 Address
  // Step 2: Replace 192.168.x.x below with your IP
  // Example: static const String baseUrl = 'http://192.168.1.10:3000/api';
  //
  // If using Android emulator use: http://10.0.2.2:3000/api
  static const String baseUrl = 'http://10.0.2.2:3000/api';

  static const String bleServiceUuid = '12345678-1234-1234-1234-123456789abc';
  static const String bleDeviceName  = 'AttendanceTeacher';
  static const int    apiTimeoutSecs = 15;
  static const int    bleScanSecs    = 10;
}
