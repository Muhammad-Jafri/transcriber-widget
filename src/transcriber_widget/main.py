import logging
import tempfile
import threading
from pathlib import Path

from .hotkey import VK_RCONTROL, PushToTalk
from .injector import inject
from .recorder import Recorder
from .transcriber import Transcriber
from .tray import State, Tray

LOG_PATH = Path(tempfile.gettempdir()) / "transcriber-widget.log"

log = logging.getLogger("transcriber_widget")


def _setup_logging() -> None:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    log.addHandler(sh)


class App:
    def __init__(self) -> None:
        self._tray = Tray()
        self._recorder = Recorder()
        self._transcriber = Transcriber()
        self._ptt = PushToTalk(VK_RCONTROL, self._on_down, self._on_up)
        self._recording = False
        self._lock = threading.Lock()

    def _load_model(self) -> None:
        cached = self._transcriber.is_model_cached()
        log.info("model cached=%s, loading...", cached)
        self._tray.update(State.LOADING if cached else State.DOWNLOADING)
        try:
            self._transcriber.load()
        except Exception as exc:
            log.exception("model load failed")
            self._tray.update(State.ERROR, str(exc))
            return
        log.info("model ready")
        self._tray.update(State.IDLE)

    def _on_down(self) -> None:
        log.info("hotkey down")
        with self._lock:
            if not self._transcriber.is_ready or self._recording:
                return
            self._recording = True
        try:
            self._recorder.start()
            self._tray.update(State.RECORDING)
        except Exception as exc:
            log.exception("recorder.start failed")
            with self._lock:
                self._recording = False
            self._tray.update(State.ERROR, str(exc))

    def _on_up(self) -> None:
        log.info("hotkey up")
        with self._lock:
            if not self._recording:
                return
            self._recording = False
        self._tray.update(State.TRANSCRIBING)
        try:
            audio = self._recorder.stop()
        except Exception as exc:
            log.exception("recorder.stop failed")
            self._tray.update(State.ERROR, str(exc))
            return
        log.info("captured %d samples", len(audio))
        threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True,
        ).start()

    def _transcribe_and_inject(self, audio) -> None:
        try:
            text = self._transcriber.transcribe(audio)
            log.info("transcribed: %r", text)
            if text:
                inject(text)
            self._tray.update(State.IDLE, text)
        except Exception as exc:
            log.exception("transcribe/inject failed")
            self._tray.update(State.ERROR, str(exc))

    def run(self) -> None:
        _setup_logging()
        log.info("starting; log file: %s", LOG_PATH)
        self._tray.set_on_quit(self._ptt.stop)
        threading.Thread(target=self._load_model, daemon=True).start()
        self._ptt.start()
        try:
            self._tray.run()
        finally:
            self._ptt.stop()


def main() -> None:
    App().run()
