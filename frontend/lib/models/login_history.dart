/// Mirrors backend src/models/user.py LoginHistory.
/// Audit trail: each login attempt (success or failure).
class LoginHistory {
  const LoginHistory({
    required this.id,
    required this.userId,
    required this.loginAt,
    this.ipAddress,
    this.userAgent,
    this.deviceFingerprint,
    required this.success,
  });

  final int id;
  final int userId;
  final DateTime loginAt;
  final String? ipAddress;
  final String? userAgent;
  final String? deviceFingerprint;
  final bool success;

  factory LoginHistory.fromJson(Map<String, dynamic> json) {
    return LoginHistory(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      loginAt: DateTime.parse(json['login_at'] as String),
      ipAddress: json['ip_address'] as String?,
      userAgent: json['user_agent'] as String?,
      deviceFingerprint: json['device_fingerprint'] as String?,
      success: json['success'] as bool,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'login_at': loginAt.toIso8601String(),
        'ip_address': ipAddress,
        'user_agent': userAgent,
        'device_fingerprint': deviceFingerprint,
        'success': success,
      };
}
