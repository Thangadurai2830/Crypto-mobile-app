/// Mirrors backend src/models/user.py Session.
/// User session: JWT id (jti) + device fingerprint for logout / invalidation.
class Session {
  const Session({
    required this.id,
    required this.userId,
    required this.jti,
    this.refreshJti,
    this.deviceFingerprint,
    this.ipAddress,
    this.userAgent,
    required this.createdAt,
    required this.expiresAt,
    this.revokedAt,
  });

  final int id;
  final int userId;
  final String jti;
  final String? refreshJti;
  final String? deviceFingerprint;
  final String? ipAddress;
  final String? userAgent;
  final DateTime createdAt;
  final DateTime expiresAt;
  final DateTime? revokedAt;

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      jti: json['jti'] as String,
      refreshJti: json['refresh_jti'] as String?,
      deviceFingerprint: json['device_fingerprint'] as String?,
      ipAddress: json['ip_address'] as String?,
      userAgent: json['user_agent'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      expiresAt: DateTime.parse(json['expires_at'] as String),
      revokedAt: json['revoked_at'] != null ? DateTime.tryParse(json['revoked_at'] as String) : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'jti': jti,
        'refresh_jti': refreshJti,
        'device_fingerprint': deviceFingerprint,
        'ip_address': ipAddress,
        'user_agent': userAgent,
        'created_at': createdAt.toIso8601String(),
        'expires_at': expiresAt.toIso8601String(),
        'revoked_at': revokedAt?.toIso8601String(),
      };
}
