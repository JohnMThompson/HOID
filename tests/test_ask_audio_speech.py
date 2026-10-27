"""Spoken confirmation must not change action execution or exit status."""

from hoid import cli, stt, tts


class FakeClient:
    def __init__(self, config):
        pass
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def turn_on(self, device):
        assert device == "desk_lamp"
        return "on"


def test_ask_audio_speaks_verified_response(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(stt, "transcribe_file", lambda _: "Turn on the desk lamp.")
    monkeypatch.setattr(cli, "load_config", lambda: object())
    monkeypatch.setattr(cli, "HomeAssistantClient", FakeClient)
    output = tmp_path / "reply.wav"
    def fake_synthesize(text, path, **kwargs):
        assert text == "The desk lamp is verified on."
        assert path == str(output)
        assert kwargs["voice"] == "bm_lewis"
        return output
    monkeypatch.setattr(tts, "synthesize_to_wav", fake_synthesize)
    assert cli.main(["ask-audio", "request.wav", "--speak", "--output", str(output),
                     "--model", "model.onnx", "--voices", "voices.bin"]) == 0
    assert capsys.readouterr().out == (
        "The desk lamp is verified on.\n"
        f"Speech written to {output}.\n"
    )


def test_ask_audio_speech_failure_does_not_undo_action(monkeypatch, capsys, tmp_path):
    actions = []
    class RecordingClient(FakeClient):
        def turn_on(self, device):
            actions.append(device)
            return "on"
    monkeypatch.setattr(stt, "transcribe_file", lambda _: "Turn on the desk lamp.")
    monkeypatch.setattr(cli, "load_config", lambda: object())
    monkeypatch.setattr(cli, "HomeAssistantClient", RecordingClient)
    def fail(*args, **kwargs):
        raise tts.SpeechError("Speech synthesis failed.")
    monkeypatch.setattr(tts, "synthesize_to_wav", fail)
    assert cli.main(["ask-audio", "request.wav", "--speak", "--output", str(tmp_path / "reply.wav"),
                     "--model", "model.onnx", "--voices", "voices.bin"]) == 0
    captured = capsys.readouterr()
    assert actions == ["desk_lamp"]
    assert "The desk lamp is verified on." in captured.out
    assert "Warning: action completed, but speech failed:" in captured.err


def test_ask_audio_unsupported_does_not_synthesize(monkeypatch, capsys):
    monkeypatch.setattr(stt, "transcribe_file", lambda _: "Please open the garage.")
    monkeypatch.setattr(tts, "synthesize_to_wav", lambda *a, **k: (_ for _ in ()).throw(AssertionError("unexpected synthesis")))
    assert cli.main(["ask-audio", "request.wav", "--speak", "--output", "/tmp/reply.wav",
                     "--model", "model.onnx", "--voices", "voices.bin"]) == 2
    assert capsys.readouterr().out == "I don't recognize that request.\n"
