
#!/usr/bin/env python3
"""HOID telephone orchestration via Asterisk FastAGI."""

import logging
import socketserver
import subprocess
import uuid
from pathlib import Path
import os

BASE = Path("/srv/services/asterisk")
RECORDINGS = BASE / "recordings"
SOUNDS = BASE / "sounds/custom"

# Asterisk's path to the same bind-mounted recording directory.
ASTERISK_RECORDINGS = "/var/spool/asterisk/recording"

HOID = "/srv/apps/hoid/.venv/bin/hoid"
MODEL = "/opt/hoid/models/kokoro/kokoro-v1.0.onnx"
VOICES = "/opt/hoid/models/kokoro/voices-v1.0.bin"
ENV_FILE = Path("/srv/apps/hoid/.env")


def load_environment():
    """Load the existing Home Assistant token-file setting."""
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()

        if line.startswith("HOID_HA_TOKEN_FILE="):
            value = line.split("=", 1)[1].strip()
            os.environ["HOID_HA_TOKEN_FILE"] = (
                value.strip('"').strip("'")
            )
            return

    raise RuntimeError(
        "HOID_HA_TOKEN_FILE not found in .env"
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


class CallEnded(Exception):
    """The caller hung up or the AGI connection ended."""


class HOIDHandler(socketserver.StreamRequestHandler):

    def command(self, instruction):
        """Send an AGI command and read its response."""
        self.wfile.write((instruction + "\n").encode())
        self.wfile.flush()

        while True:
            response = self.rfile.readline()

            if not response:
                raise CallEnded("AGI connection closed")

            response = response.decode(
                errors="replace"
            ).strip()

            if response == "HANGUP":
                raise CallEnded("Caller hung up")

            if response.startswith("200 result="):
                logging.info("AGI: %s", response)

                if response.startswith("200 result=-1"):
                    raise CallEnded(
                        "AGI command failed or call ended"
                    )

                return response

            if response.startswith(("510 ", "511 ", "520 ")):
                raise RuntimeError(
                    f"AGI error: {response}"
                )

    def handle(self):
        """Handle one telephone call."""

        # Read the AGI environment supplied by Asterisk.
        while True:
            line = self.rfile.readline()

            if not line or line in (b"\n", b"\r\n"):
                break

        call_id = uuid.uuid4().hex

        # Host-side file paths.
        recording = RECORDINGS / f"hoid-{call_id}.wav"
        raw_reply = RECORDINGS / f"reply-{call_id}.wav"

        reply_name = f"hoid-reply-{call_id}"
        reply = SOUNDS / f"{reply_name}.wav"

        # Container-side recording path, without extension.
        asterisk_recording = (
            f"{ASTERISK_RECORDINGS}/hoid-{call_id}"
        )

        logging.info("HOID call started: %s", call_id)

        try:
            # Play Lewis's greeting.
            self.command(
                'STREAM FILE custom/hoid-greeting ""'
            )

            # Record up to 15 seconds of speech.
            # Press # to stop recording early.
            # Silence detection stops after 3 seconds.
            self.command(
                f'RECORD FILE {asterisk_recording} '
                'wav "#" 15000 0 BEEP s=3'
            )

            if (
                not recording.exists()
                or recording.stat().st_size < 1000
            ):
                logging.warning("No usable recording")
                return

            logging.info(
                "Processing recording: %s",
                recording,
            )

            # Whisper -> intent -> Home Assistant -> Kokoro.
            result = subprocess.run(
                [
                    HOID,
                    "ask-audio",
                    str(recording),
                    "--speak",
                    "--model",
                    MODEL,
                    "--voices",
                    VOICES,
                    "--voice",
                    "bm_lewis",
                    "--output",
                    str(raw_reply),
                ],
                capture_output=True,
                text=True,
                timeout=90,
                check=True,
            )

            logging.info(
                "HOID output: %s",
                result.stdout.strip(),
            )

            # Convert Kokoro's output to Asterisk-compatible WAV.
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

            # Play Lewis's response over the telephone.
            self.command(
                f'STREAM FILE custom/{reply_name} ""'
            )

            logging.info(
                "HOID call completed: %s",
                call_id,
            )

        except CallEnded as exc:
            logging.info(
                "Call ended: %s",
                exc,
            )

        except subprocess.CalledProcessError as exc:
            logging.error(
                "HOID command failed (exit %s)\nstdout:\n%s\nstderr:\n%s",
                exc.returncode,
                exc.stdout,
                exc.stderr,
            )

        except (
            subprocess.SubprocessError,
            OSError,
            RuntimeError,
        ) as exc:
            logging.exception(
                "HOID processing failed: %s",
                exc,
            )

        finally:
            # No persistent recordings or generated replies.
            for path in (
		recording,
                raw_reply,
                reply,
            ):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logging.exception(
                        "Unable to remove temporary file: %s",
                        path,
                    )


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    load_environment()

    with Server(
        ("127.0.0.1", 4573),
        HOIDHandler,
    ) as server:
        logging.info(
            "HOID FastAGI listening on 127.0.0.1:4573"
        )
        server.serve_forever()
