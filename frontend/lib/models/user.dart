/// Mirrors backend src/models/user.py AccountStatus.
enum AccountStatus {
  pendingVerification('pending_verification'),
  pendingKyc('pending_kyc'),
  active('active'),
  suspended('suspended'),
  deactivated('deactivated');

  const AccountStatus(this.value);
  final String value;

  static AccountStatus? fromString(String v) {
    for (final e in AccountStatus.values) {
      if (e.value == v) return e;
    }
    return null;
  }
}

/// Mirrors backend src/models/user.py KycLevel.
enum KycLevel {
  none('none'),
  basic('basic'),
  standard('standard'),
  enhanced('enhanced');

  const KycLevel(this.value);
  final String value;

  static KycLevel? fromString(String v) {
    for (final e in KycLevel.values) {
      if (e.value == v) return e;
    }
    return null;
  }
}

/// Mirrors backend UserProfileResponse / src/models/user.py UserProfile.
class UserProfile {
  const UserProfile({
    this.displayName,
    this.firstName,
    this.lastName,
    this.phone,
    required this.kycLevel,
    this.timezone,
    this.locale,
  });

  final String? displayName;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String kycLevel;
  final String? timezone;
  final String? locale;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      displayName: json['display_name'] as String?,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      phone: json['phone'] as String?,
      kycLevel: json['kyc_level'] as String? ?? 'none',
      timezone: json['timezone'] as String?,
      locale: json['locale'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'display_name': displayName,
        'first_name': firstName,
        'last_name': lastName,
        'phone': phone,
        'kyc_level': kycLevel,
        'timezone': timezone,
        'locale': locale,
      };
}

/// Mirrors backend UserResponse / src/models/user.py User.
class User {
  const User({
    required this.id,
    required this.email,
    required this.accountStatus,
    required this.isEmailVerified,
    required this.createdAt,
    this.lastLoginAt,
    this.profile,
  });

  final int id;
  final String email;
  final String accountStatus;
  final bool isEmailVerified;
  final DateTime createdAt;
  final DateTime? lastLoginAt;
  final UserProfile? profile;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String,
      accountStatus: json['account_status'] as String? ?? 'pending_verification',
      isEmailVerified: json['is_email_verified'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      lastLoginAt: json['last_login_at'] != null ? DateTime.tryParse(json['last_login_at'] as String) : null,
      profile: json['profile'] != null ? UserProfile.fromJson(json['profile'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'account_status': accountStatus,
        'is_email_verified': isEmailVerified,
        'created_at': createdAt.toIso8601String(),
        'last_login_at': lastLoginAt?.toIso8601String(),
        'profile': profile?.toJson(),
      };
}
