#!/usr/bin/env python3
"""Generate prerecorded HOID dialogue using Kokoro."""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from fastagi import MODEL, VOICES, SOUNDS
from hoid.tts import synthesize_to_wav


BASE = Path(__file__).resolve().parent.parent
MANIFEST = BASE / "config/dialogue.json"
OUTPUT = SOUNDS / "hoid"


def generate(category, index, phrase, overwrite=False):
    """Generate one Asterisk-compatible dialogue recording."""
    directory = OUTPUT / category
    directory.mkdir(parents=True, exist_ok=True)

    destination = directory / f"{category}-{index:02d}.wav"

    if destination.exists() and not overwrite:
        print(f"  SKIP {destination.name}")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        raw = Path(temp_dir) / "raw.wav"

        synthesize_to_wav(
            phrase,
            raw,
            model_path=MODEL,
            voices_path=VOICES,
            voice="bm_lewis",
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
                str(destination),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

    print(f"  OK   {destination.name}: {phrase}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate HOID canned dialogue audio"
    )
    parser.add_argument(
        "--category",
        help="Generate only one category, e.g. greetings",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate existing recordings",
    )
    args = parser.parse_args()

    with MANIFEST.open(encoding="utf-8") as file:
        dialogue = json.load(file)

    if args.category and args.category not in dialogue:
        parser.error(f"Unknown category: {args.category}")

    categories = (
        [args.category] if args.category else list(dialogue)
    )

    for category in categories:
        phrases = dialogue[category]
        print(f"\nGenerating {category} ({len(phrases)} phrases)")

        for index, phrase in enumerate(phrases, start=1):
            generate(
                category,
                index,
                phrase,
                overwrite=args.overwrite,
            )

    print("\nDialogue generation complete.")


if __name__ == "__main__":
    main()
