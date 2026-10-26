"""Runtime configuration parsing for HOID."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from .errors import ConfigurationError

_ENTITY_ID = re.compile(r"^switch\.[a-z0-9_]+$")
_ACTIONS = {"get_state", "turn_on", "turn_off"}


@dataclass(frozen=True)
class Device:
    logical_name: str
    entity_id: str
    actions: frozenset[str]


@dataclass(frozen=True)
class RuntimeConfig:
    api_url: str
    token: str
    devices: Mapping[str, Device]
    timeout_seconds: float = 5.0
    verification_timeout_seconds: float = 2.0
    verification_interval_seconds: float = 0.2


def load_config(path: str | Path | None = None, *, environ: Mapping[str, str] | None = None) -> RuntimeConfig:
    """Load config JSON and secrets from environment; never embeds credentials."""
    env = os.environ if environ is None else environ
    config_path = Path(path or env.get("HOID_CONFIG", "hoid.json"))
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError("Configuration file is missing.") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError("Configuration file could not be read or parsed.") from exc
    if not isinstance(raw, dict):
        raise ConfigurationError("Configuration must be a JSON object.")

    api_url = env.get("HOID_HA_URL", raw.get("api_url"))
    token = env.get("HOID_HA_TOKEN")
    token_file = env.get("HOID_HA_TOKEN_FILE")
    if token and token_file:
        raise ConfigurationError("Set only one Home Assistant token source.")
    if token_file:
        try:
            token = Path(token_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ConfigurationError("Home Assistant token file could not be read.") from exc
    if not isinstance(api_url, str):
        raise ConfigurationError("Home Assistant API URL is missing.")
    parts = urlsplit(api_url)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
        raise ConfigurationError("Home Assistant API URL is invalid.")
    if not token:
        raise ConfigurationError("Home Assistant token is missing; set HOID_HA_TOKEN or HOID_HA_TOKEN_FILE.")

    raw_devices = raw.get("devices")
    if not isinstance(raw_devices, dict) or not raw_devices:
        raise ConfigurationError("At least one configured device is required.")
    devices: dict[str, Device] = {}
    seen_entities: set[str] = set()
    for name, value in raw_devices.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ConfigurationError("Device logical names must be lowercase identifiers.")
        if not isinstance(value, dict):
            raise ConfigurationError(f"Device configuration for {name} is invalid.")
        entity_id, actions = value.get("entity_id"), value.get("actions")
        if not isinstance(entity_id, str) or not _ENTITY_ID.fullmatch(entity_id):
            raise ConfigurationError(f"Device {name} must use a switch entity ID.")
        if entity_id in seen_entities:
            raise ConfigurationError("Each configured device must have a unique entity ID.")
        if not isinstance(actions, list) or not actions or any(a not in _ACTIONS for a in actions):
            raise ConfigurationError(f"Device {name} has an invalid permitted action set.")
        devices[name] = Device(name, entity_id, frozenset(actions))
        seen_entities.add(entity_id)

    return RuntimeConfig(api_url.rstrip("/"), token, devices)
