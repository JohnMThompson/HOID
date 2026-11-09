"""Tests for HOID's conversational orchestration."""

import pytest

from hoid.conversation import converse
from hoid.tools import ToolError


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def chat(self, messages, tools=None):
        self.requests.append({
            "messages": list(messages),
            "tools": tools,
        })
        return next(self.responses)


class FakeController:
    def __init__(self):
        self.calls = []

    def start_timer(self, device, duration_seconds):
        self.calls.append((device, duration_seconds))
        return "00:05:00"


def tool_call(name, arguments):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": name,
                    "arguments": arguments,
                }
            }
        ],
    }


def test_verified_timer_conversation():
    model = FakeModel([
        tool_call("start_timer", {"duration_seconds": 300}),
        {
            "role": "assistant",
            "content": "Very well. Five minutes it is.",
        },
    ])
    controller = FakeController()

    result = converse(
        "Give me five minutes before ringing.",
        model,
        controller,
    )

    assert result == "Very well. Five minutes it is."
    assert controller.calls == [("office_timer", 300)]
    assert len(model.requests) == 2

    followup_messages = model.requests[1]["messages"]

    assert followup_messages[-1]["role"] == "tool"
    assert "verified" in followup_messages[-1]["content"]


def test_conversation_without_tool():
    model = FakeModel([
        {
            "role": "assistant",
            "content": "A fine day for a little woodworking.",
        }
    ])
    controller = FakeController()

    result = converse(
        "What should I work on today?",
        model,
        controller,
    )

    assert result == "A fine day for a little woodworking."
    assert controller.calls == []
    assert len(model.requests) == 1


def test_unsupported_tool_never_executes():
    model = FakeModel([
        tool_call("delete_everything", {}),
    ])
    controller = FakeController()

    with pytest.raises(ToolError):
        converse("Delete everything.", model, controller)

    assert controller.calls == []


def test_multiple_tool_calls_never_execute():
    response = tool_call(
        "start_timer",
        {"duration_seconds": 300},
    )
    response["tool_calls"].append(
        {
            "function": {
                "name": "start_timer",
                "arguments": {"duration_seconds": 600},
            }
        }
    )

    model = FakeModel([response])
    controller = FakeController()

    with pytest.raises(ToolError):
        converse("Start two timers.", model, controller)

    assert controller.calls == []


def test_invalid_duration_never_executes():
    model = FakeModel([
        tool_call("start_timer", {"duration_seconds": -10}),
    ])
    controller = FakeController()

    with pytest.raises(ToolError):
        converse("Set a negative timer.", model, controller)

    assert controller.calls == []
