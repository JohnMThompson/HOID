import json

import httpx
import pytest

from hoid.client import HomeAssistantClient
from hoid.config import Device, RuntimeConfig, load_config
from hoid.errors import (AuthenticationError, DeviceError, EntityNotFound,
                         EntityUnavailable, HomeAssistantUnavailable,
                         OutcomeUncertain, VerificationFailed)


def config(actions=frozenset({"get_state", "turn_on", "turn_off"}), **kwargs):
    return RuntimeConfig("http://example.invalid", "synthetic-token",
                         {"desk_lamp": Device("desk_lamp", "switch.example_lamp", actions)},
                         verification_timeout_seconds=0.4,
                         verification_interval_seconds=0.1, **kwargs)


def client(responses, *, cfg=None, handler=None):
    calls = []
    def respond(request):
        calls.append(request)
        if handler:
            return handler(request, len(calls))
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
    http = httpx.Client(transport=httpx.MockTransport(respond))
    now = [0.0]
    def advance(seconds):
        now[0] += seconds
    return HomeAssistantClient(cfg or config(), http_client=http, sleep=advance,
                               monotonic=lambda: now[0]), calls


def state(value):
    return httpx.Response(200, json={"state": value})


def test_successful_state_read():
    c, calls = client([state("on")])
    assert c.get_state("desk_lamp") == "on"
    assert calls[0].url.path == "/api/states/switch.example_lamp"


@pytest.mark.parametrize(("action", "expected"), [("turn_on", "on"), ("turn_off", "off")])
def test_command_requires_and_accepts_readback(action, expected):
    c, calls = client([httpx.Response(200, json=[]), state(expected)])
    assert getattr(c, action)("desk_lamp") == expected
    assert calls[0].method == "POST"
    assert calls[0].url.path == f"/api/services/switch/{action}"


def test_unknown_or_unauthorized_never_requests():
    c, calls = client([], cfg=config(frozenset({"get_state"})))
    with pytest.raises(DeviceError):
        c.turn_on("desk_lamp")
    with pytest.raises(DeviceError):
        c.get_state("other")
    assert calls == []


def test_authentication_failure_has_no_secret():
    c, _ = client([httpx.Response(401, text="synthetic-token")])
    with pytest.raises(AuthenticationError) as exc:
        c.get_state("desk_lamp")
    assert "synthetic-token" not in str(exc.value)


@pytest.mark.parametrize("response, error", [(httpx.Response(404), EntityNotFound),
                                               (state("unavailable"), EntityUnavailable),
                                               (state("unknown"), EntityUnavailable)])
def test_missing_and_unavailable_entities(response, error):
    c, _ = client([response])
    with pytest.raises(error):
        c.get_state("desk_lamp")


@pytest.mark.parametrize("failure", [httpx.ConnectError("synthetic-token"), httpx.ReadTimeout("secret")])
def test_transport_errors_are_safe(failure):
    c, _ = client([failure])
    with pytest.raises(HomeAssistantUnavailable) as exc:
        c.get_state("desk_lamp")
    assert "synthetic-token" not in str(exc.value)
    assert "secret" not in str(exc.value)


def test_failed_verification_is_explicit_and_no_retry():
    c, calls = client([], handler=lambda req, i: (httpx.Response(200, json=[]) if i == 1 else state("off")))
    with pytest.raises(VerificationFailed):
        c.turn_on("desk_lamp")
    assert sum(r.method == "POST" for r in calls) == 1


def test_uncertain_verification_when_state_unavailable():
    c, _ = client([], handler=lambda req, i: (httpx.Response(200, json=[]) if i == 1 else state("unknown")))
    with pytest.raises(OutcomeUncertain):
        c.turn_on("desk_lamp")


def test_delayed_verification_succeeds():
    c, _ = client([], handler=lambda req, i: (httpx.Response(200, json=[]) if i == 1 else
                                              state("off" if i == 2 else "on")))
    assert c.turn_on("desk_lamp") == "on"


def test_config_loads_token_only_from_environment(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"api_url": "http://ha.example.invalid", "devices": {
        "desk_lamp": {"entity_id": "switch.example_lamp", "actions": ["get_state"]}}}))
    loaded = load_config(path, environ={"HOID_HA_TOKEN": "synthetic-token"})
    assert loaded.token == "synthetic-token"


def test_invalid_domain_and_missing_token_are_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"api_url": "http://ha.example.invalid", "devices": {
        "desk_lamp": {"entity_id": "light.example_lamp", "actions": ["get_state"]}}}))
    with pytest.raises(Exception, match="switch"):
        load_config(path, environ={"HOID_HA_TOKEN": "synthetic-token"})
    path.write_text(json.dumps({"api_url": "http://ha.example.invalid", "devices": {
        "desk_lamp": {"entity_id": "switch.example_lamp", "actions": ["get_state"]}}}))
    with pytest.raises(Exception, match="token"):
        load_config(path, environ={})
