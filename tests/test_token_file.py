"""Tests for file-backed runtime credentials."""

import json

import pytest

from hoid.config import load_config
from hoid.errors import ConfigurationError


def _config(tmp_path):
    path = tmp_path / "hoid.json"
    path.write_text(json.dumps({
        "api_url": "http://home-assistant.example.invalid:8123",
        "devices": {"desk_lamp": {
            "entity_id": "switch.example_lamp",
            "actions": ["get_state", "turn_on", "turn_off"]
        }}
    }))
    return path


def test_token_file(tmp_path):
    token = tmp_path / "token"
    token.write_text("example-secret\n")
    config = load_config(_config(tmp_path), environ={"HOID_HA_TOKEN_FILE": str(token)})
    assert config.token == "example-secret"


def test_token_file_missing(tmp_path):
    with pytest.raises(ConfigurationError, match="could not be read"):
        load_config(_config(tmp_path), environ={"HOID_HA_TOKEN_FILE": str(tmp_path / "missing")})


def test_token_sources_mutually_exclusive(tmp_path):
    token = tmp_path / "token"
    token.write_text("example-secret")
    with pytest.raises(ConfigurationError, match="only one"):
        load_config(_config(tmp_path), environ={
            "HOID_HA_TOKEN": "example-other",
            "HOID_HA_TOKEN_FILE": str(token)
        })


def test_empty_token_file(tmp_path):
    token = tmp_path / "token"
    token.write_text("\n")
    with pytest.raises(ConfigurationError, match="token is missing"):
        load_config(_config(tmp_path), environ={"HOID_HA_TOKEN_FILE": str(token)})
