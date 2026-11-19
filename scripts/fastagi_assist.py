#!/usr/bin/env python3
"""Experimental HOID FastAGI using Home Assistant Assist."""

import logging
import random
import subprocess
import uuid

from fastagi import (
    HOIDHandler,
    Server,
    CallEnded,
    RECORDINGS,
    SOUNDS,
    ASTERISK_RECORDINGS,
    MODEL,
    VOICES,
    load_environment,
)
from assist_bridge import converse
from hoid.stt import transcribe_file
from hoid.tts import synthesize_to_wav


def is_farewell(transcript):
    """Recognize short, explicit conversational endings."""
    import re

    text = transcript.lower().strip()
    text = re.sub("[^a-z0-9 ]", " ", text)
    text = " ".join(text.split())

    text = text.replace("good bye", "goodbye")
    text = text.replace("that s", "thats")
    text = text.replace("i m", "im")

    # Remove common conversational openings.
    for _ in range(2):
        for prefix in ("okay ", "ok ", "well ", "thanks ", "thank you "):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        else:
            break

    # Accept common speech-to-text variations of Hoid.
    for name in ("hoid", "hoyd", "lloyd", "hood", "boyd", "void"):
        if text.endswith(" " + name):
            text = text[:-(len(name) + 1)]
            break

    return text in {
        "goodbye",
        "bye",
        "thats all",
        "that is all",
        "im done",
        "im done for now",
        "i am done",
        "i am done for now",
        "talk to you later",
        "see you later",
    }



# Remember the previous selection across calls.
_last_dialogue_selection = {}


def select_dialogue(category):
    """Choose a prerecorded phrase without immediate repetition."""
    directory = SOUNDS / "hoid" / category
    recordings = sorted(directory.glob("*.wav"))

    if not recordings:
        return None

    previous = _last_dialogue_selection.get(category)
    candidates = [
        recording for recording in recordings
        if recording.name != previous
    ]

    selected = random.choice(candidates or recordings)
    _last_dialogue_selection[category] = selected.name

    return f"custom/hoid/{category}/{selected.stem}"


class AssistHandler(HOIDHandler):
    """Handle one Assist-backed telephone exchange."""

    def handle(self):
        # Consume the Asterisk AGI environment.
        while True:
            line = self.rfile.readline()
            if not line or line in (b"\n", b"\r\n"):
                break

        call_id = uuid.uuid4().hex
        conversation_id = None

        logging.info("Experimental Assist call started: %s", call_id)

        try:
            greeting = select_dialogue("greetings") or "custom/hoid-greeting"
            self.command(f'STREAM FILE {greeting} ""')

            turn = 0
            missed_responses = 0

            while True:
                turn += 1
                turn_id = f"{call_id}-{turn}"

                recording = RECORDINGS / f"assist-{turn_id}.wav"
                raw_reply = RECORDINGS / f"assist-raw-{turn_id}.wav"

                reply_name = f"assist-reply-{turn_id}"
                reply = SOUNDS / f"{reply_name}.wav"

                asterisk_recording = (
                    f"{ASTERISK_RECORDINGS}/assist-{turn_id}"
                )

                logging.info("Assist turn %d started", turn)

                try:
                    self.command(
                        f'RECORD FILE {asterisk_recording} '
                        'wav "#" 15000 0 s=2'
                    )

                    if (
                        not recording.exists()
                        or recording.stat().st_size < 1000
                    ):
                        transcript = None
                    else:
                        transcript = transcribe_file(recording)

                    if not transcript:
                        missed_responses += 1

                        if missed_responses >= 2:
                            logging.info(
                                "Two missed responses; ending conversation"
                            )
                            break

                        logging.info(
                            "No speech recognized; prompting caller"
                        )
                        check_in = select_dialogue("check_ins") or "custom/hoid-still-there"
                        self.command(f'STREAM FILE {check_in} ""')
                        continue

                    missed_responses = 0

                    # Never log transcripts or conversation content.
                    logging.info("Speech transcribed successfully")

                    if is_farewell(transcript):
                        logging.info("Farewell detected; ending call")
                        farewell = select_dialogue("farewells")
                        if farewell:
                            self.command(f'STREAM FILE {farewell} ""')
                        break

                    speech, conversation_id = converse(
                        transcript,
                        conversation_id=conversation_id,
                    )

                    if not speech:
                        raise RuntimeError("Assist returned no speech")

                    logging.info(
                        "Assist response received; session active: %s",
                        bool(conversation_id),
                    )

                    synthesize_to_wav(
                        speech,
                        raw_reply,
                        model_path=MODEL,
                        voices_path=VOICES,
                        voice="bm_lewis",
                    )

                    subprocess.run(
                        [
                            "ffmpeg",
                            "-nostdin",
                            "-y",
                            "-i",
                            str(raw_reply),
                            "-ar",
                            "8000",
                            "-ac",
                            "1",
                            "-c:a",
                            "pcm_s16le",
                            str(reply),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )

                    self.command(
                        f'STREAM FILE custom/{reply_name} ""'
                    )

                    logging.info("Assist turn %d completed", turn)


                finally:
                    for audio_path in (recording, raw_reply, reply):
                        try:
                            audio_path.unlink(missing_ok=True)
                        except OSError:
                            logging.exception(
                                "Unable to remove temporary audio file"
                            )

            logging.info(
                "Experimental Assist call completed: %s",
                call_id,
            )

        except CallEnded:
            logging.info("Experimental Assist call ended")

        except Exception:
            logging.exception("Experimental Assist call failed")


if __name__ == "__main__":
    load_environment()

    with Server(
        ("127.0.0.1", 4574),
        AssistHandler,
    ) as server:
        logging.info(
            "Experimental HOID Assist listening on 127.0.0.1:4574"
        )
        server.serve_forever()
