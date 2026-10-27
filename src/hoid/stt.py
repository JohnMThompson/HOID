"""Offline, file-based speech recognition using faster-whisper.

No recordings or transcripts are stored by this module.
"""

from __future__ import annotations

from pathlib import Path


class TranscriptionError(Exception):
    """The requested audio could not be transcribed."""


def transcribe_file(
    audio_path: str | Path,
    *,
    model_name: str = "tiny.en",
    model_factory=None,
) -> str:
    """Return recognized English text from an existing audio file.

    The model is loaded lazily so normal lamp commands need no STT dependencies.
    A factory can be supplied for isolated tests.
    """
    path = Path(audio_path)
    if not path.is_file():
        raise TranscriptionError("Audio file does not exist or is not a regular file.")

    if model_factory is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError(
                "Speech recognition is not installed. Install HOID with the stt extra."
            ) from exc
        model_factory = WhisperModel

    try:
        model = model_factory(model_name, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(path), beam_size=1, language="en")
        # faster-whisper transcribes lazily; consuming the generator is required.
        return " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:
        raise TranscriptionError("Audio transcription failed.") from exc
