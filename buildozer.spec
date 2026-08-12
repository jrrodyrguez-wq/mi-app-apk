[app]

# (str) Title of your application
title = Generador De Tickets

# (str) Package name (NO CAMBIAR - Mantiene la identidad de la app)
package.name = sistemapos

# (str) Package domain (NO CAMBIAR - Mantiene la identidad de la app)
package.domain = com.jrrodriguez

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db,sqlite3

# (str) Application versioning (INCREMENTADO PARA PERMITIR ACTUALIZACIÓN)
version = 0.2

# (list) Application requirements
requirements = python3,kivy,sqlite3,pyjnius

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions necesarios para Bluetooth y Android moderno
android.permissions = INTERNET, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# Permiso adicional para que la búsqueda Bluetooth funcione sin pedir ubicación estricta en Android 12+
android.extra_manifest_xml = <uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />

# (int) Target Android API
android.api = 34

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK architecture to build for
android.archs = arm64-v8a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

[buildozer]

# (int) Log level
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 0
