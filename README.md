# transcriber-widget

A lightweight Windows push-to-talk voice transcriber. Hold **Right Ctrl**, speak, and
release — your speech is transcribed locally and pasted into whatever text box is
focused (chat apps, browsers, editors). It lives as a **system-tray icon** that never
steals focus; the icon color shows state (downloading / ready / recording / transcribing).

## Model

Transcription runs fully offline with [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
using the **`tiny`** model (CPU, `int8`). The model downloads automatically on first run
(tiny ≈ 75 MB) and is cached for later runs.

`tiny` is fast and light but trades some accuracy. **If you have a decent machine, switch
to `small`** for noticeably better transcription — edit `MODEL_SIZE` in
[`src/transcriber_widget/transcriber.py`](src/transcriber_widget/transcriber.py):

```python
MODEL_SIZE = "small"   # was "tiny"; also valid: base, medium, large-v3
```

It's the single source of truth, so that one line is the only change needed.

## Requirements

- **Windows** (the app uses Win32 APIs, PortAudio, and tray integration — it does **not**
  run on Linux/WSL).
- [uv](https://docs.astral.sh/uv/) for dependency management and building.
- A microphone.

## Run from source

```powershell
uv sync
uv run transcriber-widget
```

Click into a text box, hold **Right Ctrl**, speak, release — the text is pasted in.
Right-click the tray icon to quit.

## Build a standalone .exe

Produces a single admin-elevated `dist\transcriber-widget.exe` (admin lets it paste into
elevated windows too):

```powershell
uv run pyinstaller transcriber-widget.spec --clean --noconfirm
```

Optional — launch it automatically at logon (run once in an **elevated** PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File .\install-startup.ps1
```

(Remove with `uninstall-startup.ps1`.)
