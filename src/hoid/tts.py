"""Offline speech synthesis using operator-supplied Kokoro assets."""

from pathlib import Path
import wave


class SpeechError(Exception):
    pass


def synthesize_to_wav(text, output_path, *, model_path, voices_path, voice="bm_lewis", speed=1.0, engine_factory=None):
    if not text.strip():
        raise SpeechError("Text must not be empty.")
    if not 0.5 <= speed <= 2.0:
        raise SpeechError("Speed must be between 0.5 and 2.0.")
    if not Path(model_path).is_file() or not Path(voices_path).is_file():
        raise SpeechError("Kokoro model and voices files are required.")
    output = Path(output_path)
    if output.exists():
        raise SpeechError("Output file already exists.")
    if not output.parent.is_dir():
        raise SpeechError("Output directory does not exist.")
    if engine_factory is None:
        try:
            from kokoro_onnx import Kokoro
        except ImportError as exc:
            raise SpeechError("Install HOID with the tts extra.") from exc
        engine_factory = Kokoro
    created = False
    try:
        engine = engine_factory(str(model_path), str(voices_path))
        samples, sample_rate = engine.create(text, voice=voice, speed=speed, lang="en-gb")
        import numpy as np
        audio = np.asarray(samples)
        if audio.ndim != 1 or audio.size == 0 or not np.all(np.isfinite(audio)):
            raise ValueError("Invalid audio")
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
        with output.open("xb") as stream:
            created = True
            with wave.open(stream, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(int(sample_rate))
                wav.writeframes(pcm.tobytes())
        return output
    except Exception as exc:
        if created:
            output.unlink(missing_ok=True)
        raise SpeechError("Speech synthesis failed.") from exc
