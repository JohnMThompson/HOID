import wave
import pytest
from hoid.tts import SpeechError, synthesize_to_wav


class FakeEngine:
    def __init__(self, model, voices):
        pass

    def create(self, text, *, voice, speed, lang):
        import numpy as np
        assert text == "The desk lamp is on."
        assert voice == "bm_lewis"
        assert lang == "en-gb"
        return np.array([0.0, 0.5, -0.5], dtype=np.float32), 24000


def assets(tmp_path):
    model = tmp_path / "model.onnx"
    voices = tmp_path / "voices.bin"
    model.touch()
    voices.touch()
    return model, voices


def test_wav_output(tmp_path):
    model, voices = assets(tmp_path)
    path = tmp_path / "out.wav"
    assert synthesize_to_wav("The desk lamp is on.", path, model_path=model, voices_path=voices, engine_factory=FakeEngine) == path
    with wave.open(str(path), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (1, 2, 24000, 3)


def test_empty_text(tmp_path):
    with pytest.raises(SpeechError, match="empty"):
        synthesize_to_wav("  ", tmp_path / "out.wav", model_path="missing", voices_path="missing")


def test_missing_assets(tmp_path):
    with pytest.raises(SpeechError, match="required"):
        synthesize_to_wav("Hello", tmp_path / "out.wav", model_path="missing", voices_path="missing")


def test_existing_output_preserved(tmp_path):
    model, voices = assets(tmp_path)
    path = tmp_path / "out.wav"
    path.write_bytes(b"original")
    with pytest.raises(SpeechError, match="already exists"):
        synthesize_to_wav("Hello", path, model_path=model, voices_path=voices, engine_factory=FakeEngine)
    assert path.read_bytes() == b"original"


def test_invalid_speed(tmp_path):
    with pytest.raises(SpeechError, match="Speed"):
        synthesize_to_wav("Hello", tmp_path / "out.wav", model_path="missing", voices_path="missing", speed=0)
