[app]

# (str) Title of your application
title = Sistema POS Ruta

# (str) Package name
package.name = sistemapos

# (str) Package domain (needed for android packaging)
package.domain = com.jrrodriguez

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,db,sqlite3

# (str) Application versioning
version = 0.1

# (list) Application requirements
# Incluye python3, kivy y sqlite3 para tu base de datos
requirements = python3,kivy,sqlite3

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
# permissions = INTERNET

# (int) Target Android API
android.api = 34

# (int) Minimum API required
android.minapi = 24

# (str) Android NDK architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = false, 1 = true)
warn_on_root = 0
