"""Text request processor, independent of the input interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .intents import parse_intent


class DeviceController(Protocol):
    def get_state(self, device: str) -> str: ...
    def turn_on(self, device: str) -> str: ...
    def turn_off(self, device: str) -> str: ...


@dataclass(frozen=True)
class Response:
    text: str
    status: str  # verified, unsupported


def process_text(text: str, controller: DeviceController) -> Response:
    """Route only known commands to the existing allowlisted controller.

    The controller remains responsible for authorization, state verification,
    and typed errors. Unrecognized text never invokes the controller.
    """
    intent = parse_intent(text)
    if intent is None:
        return Response("I don't recognize that request.", "unsupported")
    state = getattr(controller, intent.action)(intent.device)
    if intent.action == "get_state":
        return Response(f"The desk lamp is {state}.", "verified")
    return Response(f"The desk lamp is verified {state}.", "verified")
