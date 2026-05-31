import ctypes
import logging
import time

import pyperclip

log = logging.getLogger("transcriber_widget")

_user32 = ctypes.windll.user32

# Windows virtual-key codes.
VK_CONTROL = 0x11
VK_V = 0x56
_KEYEVENTF_KEYUP = 0x0002


def _key(vk: int, up: bool = False) -> None:
    _user32.keybd_event(vk, 0, _KEYEVENTF_KEYUP if up else 0, 0)


def inject(text: str) -> None:
    pyperclip.copy(text)
    time.sleep(0.05)
    try:
        readback = pyperclip.paste()
    except Exception:
        readback = None
    log.info("clipboard set (%d chars), readback_ok=%s", len(text), readback == text)
    # Drive Ctrl+V through the Win32 input API directly (the `keyboard`
    # library's synthetic input is unreliable on this setup).
    _key(VK_CONTROL)
    _key(VK_V)
    time.sleep(0.03)
    _key(VK_V, up=True)
    _key(VK_CONTROL, up=True)
    log.info("sent ctrl+v")
