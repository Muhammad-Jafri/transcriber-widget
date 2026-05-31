# Windows Voice Transcriber Widget — Spec

## Overview
A Windows-native Python app that captures microphone input via a push-to-talk hotkey, transcribes it with faster-whisper (tiny, CPU int8), and injects the result into whatever chatbox the user was focused on. The UI is a **system-tray icon** (no on-screen window), so it never steals focus from the target window — the target's keyboard focus is intact when we simulate Ctrl+V. It ships as an **admin-elevated one-file `.exe`** so Ctrl+V injection works even into elevated windows.

---

## Architecture

```
src/transcriber_widget/
├── __init__.py
├── main.py        # App orchestrator + entry point
├── tray.py        # pystray system-tray icon (state via color)
├── hotkey.py      # Right Ctrl push-to-talk via Win32 GetAsyncKeyState polling
├── recorder.py    # sounddevice audio capture
├── transcriber.py # faster-whisper wrapper
└── injector.py    # clipboard + Ctrl+V injection

transcriber-widget.spec  # PyInstaller one-file, windowed, uac_admin=True
build.cmd                # Windows build helper -> dist\transcriber-widget.exe
```

---

## Module Specs

### `recorder.py`
- `sounddevice.InputStream(samplerate=16000, channels=1, dtype='float32')`
- `start()` clears buffer and opens stream; callback appends float32 chunks to a list
- `stop() -> np.ndarray` closes stream, returns `np.concatenate(chunks)`
- No VAD — just raw capture between key-down and key-up

### `transcriber.py`
- `WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")` — `MODEL_SIZE = "tiny"` is the single source of truth.
- Loaded eagerly in a background thread at startup. On first run the model is downloaded from HuggingFace (tiny ≈ 75 MB); subsequent runs load from the HF cache (~1s).
- `is_model_cached() -> bool` — uses `faster_whisper.utils.download_model(MODEL_SIZE, local_files_only=True)` so `main` can show DOWNLOADING (first run) vs LOADING (cached) on the tray.
- `transcribe(audio: np.ndarray) -> str` — joins all segment texts
- Exposes `is_ready: bool` flag, set True once the model is loaded

### `injector.py`
- `inject(text: str)`:
  1. `pyperclip.copy(text)` — put text in clipboard
  2. Small `time.sleep(0.05)` — let clipboard settle
  3. `keyboard.send('ctrl+v')` — paste into focused window
- No clipboard restore needed (paste is instant; overwriting it with the transcription is acceptable UX)

### `tray.py`
- `pystray.Icon` system-tray icon — no on-screen window, so nothing can steal focus.
- Icon image generated with Pillow: a filled colored circle (`_make_image(color)`) on a 64×64 transparent RGBA bitmap; color encodes state.
- States (color, tooltip label):
  - `DOWNLOADING` — blue `#2196f3`, "Downloading model…" (first run only)
  - `LOADING` — grey `#6c7086`, "Loading model…"
  - `IDLE` — green `#4caf50`, "Ready"
  - `RECORDING` — **red `#f44336`**, "Recording…" (hotkey held)
  - `TRANSCRIBING` — orange `#ff9800`, "Transcribing…"
  - `ERROR` — deep-orange `#ff5722`, "Error"
- Right-click menu: **Quit** (`set_on_quit(cb)` lets `main` unhook the keyboard before `icon.stop()`).
- `update(state, last_text="")` swaps the icon image and tooltip. The last transcription is remembered and shown in the tooltip on hover (`Ready — last: "…"`) — the only transcription feedback.
- pystray attribute writes (`icon.icon`, `icon.title`) are thread-safe, so no main-thread marshalling is needed.

### `main.py`
- `App` class wires everything:
  1. Creates `Recorder`, `Transcriber`, `Tray`
  2. Starts model loading thread: sets DOWNLOADING/LOADING (per `is_model_cached()`), then `load()`, then IDLE (or ERROR on failure — there is no console in the windowed exe, so failures must surface on the tray)
  3. Starts `hotkey.PushToTalk(VK_RCONTROL, on_down, on_up)` — a background thread that polls `GetAsyncKeyState` for Right Ctrl (Right Alt is avoided: as AltGr it activates the Windows menu bar and injects phantom Ctrl, which steals focus and breaks paste)
  4. On key-down: if model ready and not already recording → `recorder.start()`, tray → RECORDING (red)
  5. On key-up: if recording → `recorder.stop()` → spawn transcription thread
  6. Transcription thread: `transcriber.transcribe(audio)` → `injector.inject(text)` → tray → IDLE + tooltip text
  7. `app.run()` registers `tray.set_on_quit(keyboard.unhook_all)` and calls `tray.run()` (blocks on the pystray loop); unhooks the keyboard on exit
- Entry point: `def main(): App().run()`

---

## Dependencies (`pyproject.toml`)

```toml
[project]
name = "transcriber-widget"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "faster-whisper>=1.1.0",
    "sounddevice>=0.4.6",
    "numpy>=1.24",
    "pyperclip>=1.8.2",
    "pystray>=0.19",
    "Pillow>=10",
]

[project.scripts]
transcriber-widget = "transcriber_widget.main:main"
```

Dev dependency `pyinstaller>=6` (in `[tool.uv].dev-dependencies`) builds the exe.
`sounddevice` wheels bundle PortAudio for Windows — no separate install needed.  
Right Ctrl detection uses Win32 `GetAsyncKeyState` polling and paste uses Win32 `keybd_event` Ctrl+V — both via ctypes, no `keyboard` library (its hooks dropped key-up events and its synthetic input was unreliable here). The exe requests admin (`uac_admin=True`) so Ctrl+V injection reaches elevated target windows too.

---

## Threading Model

| Thread | Responsibility |
|--------|----------------|
| Main (pystray) | Tray event loop; icon/tooltip writes are thread-safe (no marshalling) |
| Hotkey poller | `PushToTalk` thread polling `GetAsyncKeyState`; fires on_down/on_up, spawns transcription threads |
| Model loader | One-shot at startup; downloads/loads the model, sets `transcriber.is_ready = True` |
| Transcription | Spawned per recording; dies after inject |
| sounddevice audio | Callback-based; just appends numpy chunks to list |

---

## Verification

### Dev run (Windows)
1. `uv sync`, then `uv run transcriber-widget`
2. Tray icon appears: **blue** "Downloading model…" on first run (else **grey** "Loading…"), then **green** "Ready"
3. Click into any chatbox (Notepad, browser chat, etc.)
4. Hold Right Ctrl → icon turns **red** ("Recording…"); speak; release → **orange** ("Transcribing…") → **green**
5. Transcribed text appears in the chatbox; hover the tray icon to see it in the tooltip
6. Focus never leaves the chatbox (no on-screen window exists)
7. Right-click tray icon → **Quit** exits cleanly

### Build (Windows)
8. `build.cmd` → `dist\transcriber-widget.exe`
9. Double-click the exe → accept the UAC prompt → same flow as above; Ctrl+V injection now works into elevated windows too

### Run at logon (Windows)
Because the exe is admin-elevated, a Startup-folder shortcut would prompt for UAC
every login (or be blocked). Instead, a Scheduled Task runs it elevated with no
prompt. From an **elevated** PowerShell, once:
```powershell
powershell -ExecutionPolicy Bypass -File .\install-startup.ps1   # register task "TranscriberWidget"
Start-ScheduledTask -TaskName TranscriberWidget                  # launch now without rebooting
```
Remove with `uninstall-startup.ps1`. The task triggers `-AtLogOn` for the current
user with `-RunLevel Highest`.
