"""Tests for the conversational tool dispatcher."""

import pytest

from hoid.tools import ToolError, execute_tool


class FakeController:
    def __init__(self):
        self.calls = []

    def start_timer(self, device, duration_seconds):
        self.calls.append((device, duration_seconds))
        return "00:05:00"


def test_valid_timer_request():
    controller = FakeController()

    result = execute_tool(
        "start_timer",
        {"duration_seconds": 300},
        controller,
    )

    assert controller.calls == [("office_timer", 300)]
    assert "5 minutes" in result
    assert "verified" in result


@pytest.mark.parametrize(
    "name, arguments",
    [
        ("delete_everything", {}),
        ("turn_on", {"device": "desk_lamp"}),
        ("start_timer", {}),
        ("start_timer", {"duration_seconds": 0}),
        ("start_timer", {"duration_seconds": 86401}),
        ("start_timer", {"duration_seconds": -30}),
        ("start_timer", {"duration_seconds": "300"}),
        ("start_timer", {"duration_seconds": True}),
        ("start_timer", {"duration_seconds": 300, "extra": 1}),
        ("start_timer", ["300"]),
    ],
)
def test_invalid_requests_never_execute(name, arguments):
    controller = FakeController()

    with pytest.raises(ToolError):
        execute_tool(name, arguments, controller)

    assert controller.calls == []


def test_controller_failure_is_not_reported_as_success():
    class FailingController:
        def start_timer(self, device, duration_seconds):
            raise RuntimeError("Timer state could not be verified")

    with pytest.raises(RuntimeError, match="could not be verified"):
        execute_tool(
            "start_timer",
            {"duration_seconds": 300},
            FailingController(),
        )
