import numpy as np
from faster_whisper import WhisperModel
from faster_whisper.utils import download_model

MODEL_SIZE = "tiny"


class Transcriber:
    def __init__(self) -> None:
        self.is_ready = False
        self._model: WhisperModel | None = None

    def is_model_cached(self) -> bool:
        try:
            download_model(MODEL_SIZE, local_files_only=True)
            return True
        except Exception:
            return False

    def load(self) -> None:
        self._model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        self.is_ready = True

    def transcribe(self, audio: np.ndarray) -> str:
        if not self.is_ready or self._model is None or len(audio) == 0:
            return ""
        segments, _ = self._model.transcribe(audio, beam_size=5)
        return " ".join(seg.text.strip() for seg in segments).strip()
