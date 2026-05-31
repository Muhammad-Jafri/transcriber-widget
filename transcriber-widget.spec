# PyInstaller spec — one-file, windowed, admin-elevated (UAC prompt on launch).
# Build on Windows: build.cmd  (-> dist\transcriber-widget.exe)
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
)

binaries = []
datas = []
hiddenimports = ["pystray._win32"]

# faster-whisper pulls in native libraries that need explicit collection.
for pkg in ("ctranslate2", "av", "onnxruntime"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# sounddevice bundles the PortAudio DLL; faster_whisper ships asset files.
binaries += collect_dynamic_libs("sounddevice")
datas += collect_data_files("sounddevice")
datas += collect_data_files("faster_whisper")


a = Analysis(
    ["launcher.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="transcriber-widget",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    uac_admin=True,
    # icon="assets/app.ico",  # optional: add an .ico to brand the exe
)
