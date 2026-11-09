"""Text request processor, independent of the input interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .intents import parse_intent


class DeviceController(Protocol):
    def get_state(self, device: str) -> str: ...
    def turn_on(self, device: str) -> str: ...
    def turn_off(self, device: str) -> str: ...
    def start_timer(self, device: str, duration_seconds: int) -> str: ...


@dataclass(frozen=True)
class Response:
    text: str
    status: str  # verified, unsupported

def format_duration(seconds: int) -> str:
    """Format a timer duration for natural speech."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    for value, unit in (
        (hours, "hour"),
        (minutes, "minute"),
        (seconds, "second"),
    ):
        if value:
            suffix = "" if value == 1 else "s"
            parts.append(f"{value} {unit}{suffix}")

    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return " and ".join(parts)

    return ", ".join(parts[:-1]) + ", and " + parts[-1]

def process_text(text: str, controller: DeviceController) -> Response:
    """Route only known commands to the existing allowlisted controller.

    The controller remains responsible for authorization, state verification,
    and typed errors. Unrecognized text never invokes the controller.
    """
    intent = parse_intent(text)
    if intent is None:
        return Response("I don't recognize that request.", "unsupported")
    if intent.action == "start_timer":
        if intent.duration_seconds is None:
            return Response("The timer duration was not understood.", "unsupported")

        controller.start_timer(
            intent.device,
            intent.duration_seconds,
        )
        spoken_duration = format_duration(intent.duration_seconds)

        return Response(
            f"Very well. Your timer is set for {spoken_duration}.",
            "verified",
        )
    state = getattr(controller, intent.action)(intent.device)
    if intent.action == "get_state":
        return Response(f"The desk lamp is {state}.", "verified")
    return Response(f"The desk lamp is verified {state}.", "verified")
