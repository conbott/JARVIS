import os
import tempfile
import logging
from typing import Optional

# Compatibility patch for PyAV >= 13/14+ where metadata_errors was removed from av.open
try:
    import av
    if hasattr(av, "open"):
        _orig_av_open = av.open
        def _compat_av_open(*args, **kwargs):
            kwargs.pop("metadata_errors", None)
            return _orig_av_open(*args, **kwargs)
        av.open = _compat_av_open
except Exception:
    pass

logger = logging.getLogger(__name__)

class STTEngine:
    def __init__(self, model_size: str = "base.en"):
        self.model_size = model_size
        self._model = None

    @property
    def model(self):
        """
        Lazy load WhisperModel on CPU with INT8 compute to conserve memory
        and ensure instant server startup.
        """
        if self._model is None:
            logger.info(f"Loading faster-whisper '{self.model_size}' model on CPU/INT8...")
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            logger.info("faster-whisper model loaded successfully.")
        return self._model

    def transcribe_audio_bytes(self, audio_bytes: bytes, suffix: str = ".webm") -> str:
        """
        Transcribes raw audio bytes captured from the browser MediaRecorder.
        Returns the recognized text string.
        """
        if not audio_bytes:
            return ""

        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(audio_bytes)
                temp_file = f.name

            segments, info = self.model.transcribe(temp_file, beam_size=2)
            transcript_parts = [segment.text for segment in segments]
            full_text = " ".join(transcript_parts).strip()
            logger.info(f"Whisper transcription ({info.language}, prob={info.language_probability:.2f}): '{full_text}'")
            return full_text
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

stt_engine = STTEngine()
