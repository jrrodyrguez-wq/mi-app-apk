[app]

title = Ruta Distribuidor
package.name = rutadistribuidor
package.domain = com.jr

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

version = 1.0

requirements = python3,kivy

orientation = portrait

fullscreen = 0

android.api = 34
android.minapi = 24
android.accept_sdk_license = True

android.permissions = INTERNET

android.archs = arm64-v8a,armeabi-v7a

android.debug_artifact = apk
android.release_artifact = apk

[buildozer]

log_level = 2
warn_on_root = 1
