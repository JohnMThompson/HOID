
"""Generate Asterisk-compatible audio for scheduler announcements."""

import subprocess
import tempfile
from pathlib import Path

from hoid.tts import synthesize_to_wav


def generate_announcement(
    message,
    destination,
    *,
    model_path,
    voices_path,
    voice="bm_lewis",
):
    """Synthesize a message as 8 kHz mono PCM WAV."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Announcement message cannot be empty.")

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=destination.parent,
        prefix=".hoid-audio-",
    ) as temp_dir:
        raw = Path(temp_dir) / "raw.wav"
        converted = Path(temp_dir) / "converted.wav"

        synthesize_to_wav(
            message,
            raw,
            model_path=model_path,
            voices_path=voices_path,
            voice=voice,
        )

        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-y",
                "-i", str(raw),
                "-ar", "8000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                str(converted),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        # Publish only after conversion succeeds.
        converted.replace(destination)

    return destination
