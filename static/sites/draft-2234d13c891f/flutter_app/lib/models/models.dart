class UserModel {
  final String id, name, email, role, token;
  final String? deviceId, rollNumber;

  UserModel({required this.id, required this.name, required this.email,
    required this.role, required this.token, this.deviceId, this.rollNumber});

  factory UserModel.fromJson(Map<String, dynamic> json, String token) {
    final u = json['user'] ?? json;
    return UserModel(
      id: u['id']?.toString() ?? u['_id']?.toString() ?? '',
      name: u['name'] ?? '', email: u['email'] ?? '',
      role: u['role'] ?? '', token: token,
      deviceId: u['deviceId'] ?? u['device_id'],
      rollNumber: u['rollNumber'] ?? u['roll_number'],
    );
  }
  bool get isTeacher => role == 'teacher';
  bool get isStudent => role == 'student';
}

class SessionModel {
  final String sessionId, subject, className;
  final DateTime endTime;
  final int rssiThreshold, windowMinutes;
  final String? teacherName;

  SessionModel({required this.sessionId, required this.subject,
    required this.className, required this.endTime,
    required this.rssiThreshold, required this.windowMinutes, this.teacherName});

  factory SessionModel.fromJson(Map<String, dynamic> json) => SessionModel(
    sessionId:     json['session_id'] ?? '',
    subject:       json['subject'] ?? '',
    className:     json['class_name'] ?? '',
    endTime:       DateTime.parse(json['end_time']),
    rssiThreshold: json['rssi_threshold'] ?? -65,
    windowMinutes: json['window_minutes'] ?? 5,
    teacherName:   json['teacher_name'],
  );

  bool get isExpired => DateTime.now().isAfter(endTime);
  Duration get timeLeft => endTime.difference(DateTime.now());
}

class AttendanceRecord {
  final String id, subject, className, status;
  final DateTime timestamp;
  final int? rssiValue;
  final String? teacherName;

  AttendanceRecord({required this.id, required this.subject,
    required this.className, required this.timestamp,
    required this.status, this.rssiValue, this.teacherName});

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) => AttendanceRecord(
    id:          json['id']?.toString() ?? '',
    subject:     json['subject'] ?? '',
    className:   json['class_name'] ?? '',
    timestamp:   DateTime.parse(json['timestamp']),
    status:      json['status'] ?? 'present',
    rssiValue:   json['rssi_value'],
    teacherName: json['teacher_name'],
  );
}

class BleTeacherDevice {
  final String deviceId;
  final int rssi;
  final String? sessionId, token;
  BleTeacherDevice({required this.deviceId, required this.rssi, this.sessionId, this.token});
}
