"""Allowlist-backed Home Assistant REST client."""

from __future__ import annotations

import time

import httpx

from .config import RuntimeConfig
from .errors import (
    AuthenticationError,
    CommandRejected,
    DeviceError,
    EntityNotFound,
    EntityUnavailable,
    HomeAssistantUnavailable,
    OutcomeUncertain,
    VerificationFailed,
)


class HomeAssistantClient:
    def __init__(self, config: RuntimeConfig, *, http_client: httpx.Client | None = None,
                 sleep=time.sleep, monotonic=time.monotonic):
        self._config = config
        self._http = http_client or httpx.Client(timeout=config.timeout_seconds)
        self._owns_http = http_client is None
        self._sleep = sleep
        self._monotonic = monotonic

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> "HomeAssistantClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_state(self, device_name: str) -> str:
        device = self._device(device_name, "get_state")
        return self._read_state(device.entity_id)

    def turn_on(self, device_name: str) -> str:
        return self._set_state(device_name, "turn_on", "on")

    def turn_off(self, device_name: str) -> str:
        return self._set_state(device_name, "turn_off", "off")

    def _device(self, name: str, action: str):
        device = self._config.devices.get(name)
        if device is None:
            raise DeviceError(f"Unknown device: {name}.")
        if action not in device.actions:
            raise DeviceError(f"Action {action} is not permitted for device {name}.")
        return device

    def _request(self, method: str, path: str, *, json_body: dict | None = None) -> httpx.Response:
        try:
            return self._http.request(method, f"{self._config.api_url}{path}",
                                      headers={"Authorization": f"Bearer {self._config.token}"},
                                      json=json_body, timeout=self._config.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise HomeAssistantUnavailable("Home Assistant request timed out.") from exc
        except httpx.RequestError as exc:
            raise HomeAssistantUnavailable("Home Assistant could not be reached.") from exc

    @staticmethod
    def _check_response(response: httpx.Response, *, command: bool = False) -> None:
        if response.status_code in (401, 403):
            raise AuthenticationError("Home Assistant rejected authentication or authorization.")
        if response.status_code == 404:
            raise EntityNotFound("The configured Home Assistant entity was not found.")
        if command and not 200 <= response.status_code < 300:
            raise CommandRejected("Home Assistant rejected the command.")
        if not command and not 200 <= response.status_code < 300:
            raise HomeAssistantUnavailable("Home Assistant returned an unexpected response.")

    def _read_state(self, entity_id: str) -> str:
        response = self._request("GET", f"/api/states/{entity_id}")
        self._check_response(response)
        try:
            state = response.json()["state"]
        except (ValueError, TypeError, KeyError) as exc:
            raise HomeAssistantUnavailable("Home Assistant returned an invalid state response.") from exc
        if not isinstance(state, str):
            raise HomeAssistantUnavailable("Home Assistant returned an invalid state response.")
        if state in {"unavailable", "unknown"}:
            raise EntityUnavailable("Home Assistant reports this entity as unavailable or unknown.")
        return state

    def _set_state(self, name: str, action: str, expected: str) -> str:
        device = self._device(name, action)
        response = self._request("POST", f"/api/services/switch/{action}",
                                 json_body={"entity_id": device.entity_id})
        self._check_response(response, command=True)
        deadline = self._monotonic() + self._config.verification_timeout_seconds
        observed: str | None = None
        while True:
            try:
                observed = self._read_state(device.entity_id)
            except (AuthenticationError, EntityNotFound) as exc:
                raise OutcomeUncertain(
                    "The command was sent, but its resulting state could not be confirmed."
                ) from exc
            except (EntityUnavailable, HomeAssistantUnavailable):
                observed = None
            if observed == expected:
                return observed
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                if observed is None:
                    raise OutcomeUncertain("The command was sent, but the resulting state could not be confirmed.")
                raise VerificationFailed(f"The command was sent, but Home Assistant still reports state {observed}.")
            self._sleep(min(self._config.verification_interval_seconds, remaining))
