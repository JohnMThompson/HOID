"""Validated tool execution for HOID's conversational assistant."""

from __future__ import annotations

from typing import Any

from .requests import DeviceController, format_duration


class ToolError(Exception):
    """The language model requested an invalid or unsupported tool."""


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    controller: DeviceController,
) -> str:
    """Execute an explicitly permitted tool with validated arguments."""

    if name != "start_timer":
        raise ToolError(f"Unsupported tool: {name}")

    if not isinstance(arguments, dict):
        raise ToolError("Tool arguments must be an object.")

    if set(arguments) != {"duration_seconds"}:
        raise ToolError("Invalid timer arguments.")

    seconds = arguments["duration_seconds"]

    if type(seconds) is not int or not 1 <= seconds <= 86400:
        raise ToolError("Timer duration must be between 1 and 86400 seconds.")

    controller.start_timer("office_timer", seconds)

    return (
        f"Timer successfully started and verified "
        f"for {format_duration(seconds)}."
    )
