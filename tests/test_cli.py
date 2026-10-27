from hoid import cli
from hoid.errors import ConfigurationError


class FakeClient:
    def __init__(self, _config): pass
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def get_state(self, device):
        assert device == "desk_lamp"
        return "on"
    def turn_on(self, device):
        assert device == "desk_lamp"
        return "on"
    def turn_off(self, device):
        assert device == "desk_lamp"
        return "off"


def test_cli_output_and_success(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_config", lambda: object())
    monkeypatch.setattr(cli, "HomeAssistantClient", FakeClient)
    assert cli.main(["lamp", "status"]) == 0
    assert capsys.readouterr().out == "Desk lamp is on.\n"
    assert cli.main(["lamp", "off"]) == 0
    assert capsys.readouterr().out == "Desk lamp verified off.\n"


def test_cli_failure_exit_code(monkeypatch, capsys):
    def fail(): raise ConfigurationError("safe configuration error")
    monkeypatch.setattr(cli, "load_config", fail)
    assert cli.main(["lamp", "on"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Error: safe configuration error\n"


def test_transcribe_cli(monkeypatch, capsys):
    from hoid import stt

    monkeypatch.setattr(stt, "transcribe_file", lambda path: "Turn on the desk lamp.")
    assert cli.main(["transcribe", "sample.wav"]) == 0
    assert capsys.readouterr().out == "Turn on the desk lamp.\n"


def test_transcribe_cli_failure(monkeypatch, capsys):
    from hoid import stt

    def fail(_path):
        raise stt.TranscriptionError("Audio transcription failed.")

    monkeypatch.setattr(stt, "transcribe_file", fail)
    assert cli.main(["transcribe", "missing.wav"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Error: Audio transcription failed.\n"
