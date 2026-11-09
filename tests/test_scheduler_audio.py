
"""Tests for HOID scheduler audio generation."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from hoid.scheduler_audio import generate_announcement


@pytest.fixture
def destination(tmp_path):
    return tmp_path / "sounds" / "tea.wav"


def test_successful_audio_generation(destination):
    def fake_synthesize(message, output, **kwargs):
        Path(output).write_bytes(b"raw audio")

    def fake_ffmpeg(command, **kwargs):
        output = Path(command[-1])
        output.write_bytes(b"converted audio")
        return subprocess.CompletedProcess(command, 0)

    with (
        patch(
            "hoid.scheduler_audio.synthesize_to_wav",
            side_effect=fake_synthesize,
        ) as synthesize,
        patch(
            "hoid.scheduler_audio.subprocess.run",
            side_effect=fake_ffmpeg,
        ),
    ):
        result = generate_announcement(
            "Your tea timer has finished.",
            destination,
            model_path="model.onnx",
            voices_path="voices.bin",
        )

    assert result == destination
    assert destination.read_bytes() == b"converted audio"
    assert synthesize.call_count == 1


def test_failed_conversion_preserves_existing_audio(destination):
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"original audio")

    def fake_synthesize(message, output, **kwargs):
        Path(output).write_bytes(b"raw audio")

    with (
        patch(
            "hoid.scheduler_audio.synthesize_to_wav",
            side_effect=fake_synthesize,
        ),
        patch(
            "hoid.scheduler_audio.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "ffmpeg"),
        ),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            generate_announcement(
                "Your tea timer has finished.",
                destination,
                model_path="model.onnx",
                voices_path="voices.bin",
            )

    assert destination.read_bytes() == b"original audio"
    assert list(destination.parent.glob(".hoid-audio-*")) == []


@pytest.mark.parametrize("message", ["", "   ", None])
def test_empty_messages_rejected(destination, message):
    with pytest.raises(ValueError):
        generate_announcement(
            message,
            destination,
            model_path="model.onnx",
            voices_path="voices.bin",
        )

    assert not destination.exists()


def test_audio_format_settings(destination):
    def fake_synthesize(message, output, **kwargs):
        Path(output).write_bytes(b"raw audio")

    def fake_ffmpeg(command, **kwargs):
        Path(command[-1]).write_bytes(b"converted audio")
        return subprocess.CompletedProcess(command, 0)

    with (
        patch(
            "hoid.scheduler_audio.synthesize_to_wav",
            side_effect=fake_synthesize,
        ),
        patch(
            "hoid.scheduler_audio.subprocess.run",
            side_effect=fake_ffmpeg,
        ) as ffmpeg,
    ):
        generate_announcement(
            "Timer finished.",
            destination,
            model_path="model.onnx",
            voices_path="voices.bin",
        )

    command = ffmpeg.call_args.args[0]

    assert command[command.index("-ar") + 1] == "8000"
    assert command[command.index("-ac") + 1] == "1"
    assert command[command.index("-c:a") + 1] == "pcm_s16le"

