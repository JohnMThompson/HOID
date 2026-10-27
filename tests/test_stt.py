from types import SimpleNamespace

import pytest

from hoid.stt import TranscriptionError, transcribe_file


def test_transcribes_file_without_real_model(tmp_path):
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"synthetic fixture")
    calls = []

    class FakeModel:
        def __init__(self, name, *, device, compute_type):
            calls.append((name, device, compute_type))

        def transcribe(self, filename, *, beam_size, language):
            assert filename == str(audio)
            assert beam_size == 1
            assert language == "en"
            return iter([SimpleNamespace(text=" Turn on "), SimpleNamespace(text="the desk lamp. ")]), None

    assert transcribe_file(audio, model_factory=FakeModel) == "Turn on the desk lamp."
    assert calls == [("tiny.en", "cpu", "int8")]


def test_missing_audio_is_safe_error(tmp_path):
    with pytest.raises(TranscriptionError, match="does not exist"):
        transcribe_file(tmp_path / "missing.wav")


def test_model_failure_does_not_expose_details(tmp_path):
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"synthetic fixture")

    def fail(*args, **kwargs):
        raise RuntimeError("private recording path or internal details")

    with pytest.raises(TranscriptionError, match="Audio transcription failed") as error:
        transcribe_file(audio, model_factory=fail)
    assert "private" not in str(error.value)
