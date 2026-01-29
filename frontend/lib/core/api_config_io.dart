import 'dart:io' show Platform;

String get apiHost => Platform.isAndroid ? '10.0.2.2' : 'localhost';
