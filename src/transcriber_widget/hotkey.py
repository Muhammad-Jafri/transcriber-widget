import ctypes
import threading
import time

# Windows virtual-key code for the Right Ctrl key. (Right Alt is avoided: as
# AltGr it activates the menu bar / injects phantom Ctrl, breaking paste.)
VK_RCONTROL = 0xA3
_KEY_DOWN_MASK = 0x8000

_user32 = ctypes.windll.user32
_user32.GetAsyncKeyState.restype = ctypes.c_short
_user32.GetAsyncKeyState.argtypes = [ctypes.c_int]


def _is_down(vk: int) -> bool:
    return bool(_user32.GetAsyncKeyState(vk) & _KEY_DOWN_MASK)


class PushToTalk:
    """Detects hold/release of a key by polling the physical key state.

    We poll ``GetAsyncKeyState`` instead of using ``keyboard`` hooks because
    the hooks proved unreliable here (they dropped modifier key-up events).
    Polling the OS reads the true hardware state, so a release is never lost.
    """

    def __init__(self, vk, on_down, on_up, poll_interval=0.02) -> None:
        self._vk = vk
        self._on_down = on_down
        self._on_up = on_up
        self._poll = poll_interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        held = False
        while not self._stop.is_set():
            down = _is_down(self._vk)
            if down and not held:
                held = True
                self._on_down()
            elif not down and held:
                held = False
                self._on_up()
            time.sleep(self._poll)
