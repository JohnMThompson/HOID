"""Minimal command line interface for HOID."""

from __future__ import annotations

import argparse
import sys

from .client import HomeAssistantClient
from .config import load_config
from .errors import HoidError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hoid")
    targets = parser.add_subparsers(dest="target", required=True)
    lamp = targets.add_parser("lamp", help="control the configured desk_lamp device")
    commands = lamp.add_subparsers(dest="action", required=True)
    commands.add_parser("status")
    commands.add_parser("on")
    commands.add_parser("off")
    transcription = targets.add_parser("transcribe", help="transcribe an audio file locally")
    transcription.add_argument("audio_file", help="path to an existing audio file")
    ask = targets.add_parser("ask", help="interpret a supported text request")
    ask.add_argument("text", help="request text in quotation marks")
    audio = targets.add_parser("ask-audio", help="transcribe and interpret a recorded command")
    audio.add_argument("audio_file", help="path to an existing audio file")
    audio.add_argument("--dry-run", action="store_true", help="show recognized intent without contacting Home Assistant")
    args = parser.parse_args(argv)

    if args.target == "transcribe":
        from .stt import TranscriptionError, transcribe_file

        try:
            print(transcribe_file(args.audio_file))
            return 0
        except TranscriptionError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if args.target in {"ask", "ask-audio"}:
        from .intents import parse_intent
        from .requests import process_text

        if args.target == "ask-audio":
            from .stt import TranscriptionError, transcribe_file

            try:
                text = transcribe_file(args.audio_file)
            except TranscriptionError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                return 1
            if not text.strip():
                print("I couldn't hear a command.")
                return 2
        else:
            text = args.text

        intent = parse_intent(text)
        if intent is None:
            print("I don't recognize that request.")
            return 2
        if args.target == "ask-audio" and args.dry_run:
            print(f"Recognized: {intent.device} / {intent.action} (dry run; no action taken)")
            return 0

        try:
            config = load_config()
            with HomeAssistantClient(config) as client:
                response = process_text(text, client)
            print(response.text)
            return 0
        except HoidError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    action = {"status": "get_state", "on": "turn_on", "off": "turn_off"}[args.action]
    try:
        config = load_config()
        with HomeAssistantClient(config) as client:
            result = getattr(client, action)("desk_lamp")
        print(f"Desk lamp is {result}." if action == "get_state" else f"Desk lamp verified {result}.")
        return 0
    except HoidError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
