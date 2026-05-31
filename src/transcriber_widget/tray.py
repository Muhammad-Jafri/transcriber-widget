from enum import Enum, auto

import pystray
from PIL import Image, ImageDraw

_RING = "#11111b"


class State(Enum):
    DOWNLOADING = auto()
    LOADING = auto()
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    ERROR = auto()


_STATE_CONFIG: dict[State, tuple[str, str]] = {
    State.DOWNLOADING:  ("#2196f3", "Downloading model…"),
    State.LOADING:      ("#6c7086", "Loading model…"),
    State.IDLE:         ("#4caf50", "Ready"),
    State.RECORDING:    ("#f44336", "Recording…"),
    State.TRANSCRIBING: ("#ff9800", "Transcribing…"),
    State.ERROR:        ("#ff5722", "Error"),
}


def _make_image(color: str) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((6, 6, 58, 58), fill=color, outline=_RING, width=3)
    return img


class Tray:
    def __init__(self) -> None:
        self._last_text = ""
        self._on_quit = None
        color, label = _STATE_CONFIG[State.LOADING]
        self._icon = pystray.Icon(
            "transcriber-widget",
            _make_image(color),
            label,
            menu=pystray.Menu(pystray.MenuItem("Quit", self._handle_quit)),
        )

    def set_on_quit(self, callback) -> None:
        self._on_quit = callback

    def _handle_quit(self) -> None:
        if self._on_quit is not None:
            self._on_quit()
        self._icon.stop()

    def update(self, state: State, last_text: str = "") -> None:
        color, label = _STATE_CONFIG[state]
        if last_text:
            self._last_text = last_text
        self._icon.icon = _make_image(color)
        if self._last_text:
            snippet = self._last_text
            if len(snippet) > 44:
                snippet = snippet[:44] + "…"
            self._icon.title = f'{label} — last: "{snippet}"'
        else:
            self._icon.title = label

    def run(self) -> None:
        self._icon.run()
