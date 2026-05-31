@echo off
REM Build the one-file, admin-elevated tray exe. Run from a Windows shell.
REM Output: dist\transcriber-widget.exe  (double-click -> UAC prompt -> runs)
cd /d "%~dp0"
uv run pyinstaller transcriber-widget.spec --clean --noconfirm
