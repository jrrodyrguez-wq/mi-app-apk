[app]
title = Sistema POS Ruta
package.name = sistemapos
package.domain = com.jrrodriguez
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,sqlite3
version = 0.1
requirements = python3,kivy,sqlite3,pyjnius
orientation = landscape
fullscreen = 0
permissions = INTERNET, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
