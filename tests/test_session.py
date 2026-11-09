import pytest

from hoid.session import ConversationSession, SessionClosed


class FakeModel:
    def __init__(self):
        self.calls = []

    def chat(self, messages, tools=None):
        self.calls.append(messages)

        if len(self.calls) == 1:
            return {
                "role": "assistant",
                "content": "Cherry is a good choice for a small bowl.",
            }

        return {
            "role": "assistant",
            "content": "A small bowl would be a manageable project.",
        }


def test_session_preserves_context():
    model = FakeModel()
    session = ConversationSession(model, controller=None)

    first = session.ask("What could I carve from cherry?")
    second = session.ask("Which would be easiest?")

    assert "small bowl" in first
    assert "small bowl" in second

    second_request = model.calls[1]

    assert second_request[1] == {
        "role": "user",
        "content": "What could I carve from cherry?",
    }
    assert second_request[2] == {
        "role": "assistant",
        "content": first,
    }
    assert second_request[3] == {
        "role": "user",
        "content": "Which would be easiest?",
    }


def test_session_trims_complete_turns():
    model = FakeModel()
    session = ConversationSession(
        model,
        controller=None,
        max_turns=2,
    )

    session.ask("First question")
    session.ask("Second question")
    session.ask("Third question")

    user_messages = [
        message["content"]
        for message in session.history
        if message["role"] == "user"
    ]

    assert user_messages == [
        "Second question",
        "Third question",
    ]


def test_session_close_discards_history():
    model = FakeModel()
    session = ConversationSession(model, controller=None)

    session.ask("Hello")
    assert session.history

    session.close()

    assert session.history == []
    assert session.closed is True

    with pytest.raises(SessionClosed):
        session.ask("Are you still there?")


def test_session_rejects_empty_input():
    session = ConversationSession(FakeModel(), controller=None)

    with pytest.raises(ValueError):
        session.ask("   ")

    assert session.history == []


def test_session_preserves_verified_tool_result():
    class ToolModel:
        def __init__(self):
            self.calls = []

        def chat(self, messages, tools=None):
            self.calls.append(messages)

            if len(self.calls) == 1:
                return {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "start_timer",
                                "arguments": {
                                    "duration_seconds": 30,
                                },
                            },
                        }
                    ],
                }

            if len(self.calls) == 2:
                return {
                    "role": "assistant",
                    "content": "I'll ring you in thirty seconds.",
                }

            return {
                "role": "assistant",
                "content": "Yes, the timer was started.",
            }

    class FakeController:
        def __init__(self):
            self.started = []

        def start_timer(self, timer_id, seconds):
            self.started.append((timer_id, seconds))

    model = ToolModel()
    controller = FakeController()
    session = ConversationSession(model, controller)

    first = session.ask("Ring me in thirty seconds.")
    second = session.ask("Did you start that timer?")

    assert first == "I'll ring you in thirty seconds."
    assert second == "Yes, the timer was started."
    assert controller.started == [("office_timer", 30)]

    followup_messages = model.calls[2]

    assert any(
        message["role"] == "tool"
        and "successfully started and verified" in message["content"]
        for message in followup_messages
    )

    assert any(
        message["role"] == "assistant"
        and message.get("tool_calls")
        for message in followup_messages
    )


def test_session_blocks_unrequested_timer():
    from hoid.authorization import ActionNotAuthorized

    class MistakenModel:
        def chat(self, messages, tools=None):
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "start_timer",
                            "arguments": {
                                "duration_seconds": 600,
                            },
                        }
                    }
                ],
            }

    class FakeController:
        def __init__(self):
            self.started = []

        def start_timer(self, timer_id, seconds):
            self.started.append((timer_id, seconds))

    controller = FakeController()
    session = ConversationSession(MistakenModel(), controller)

    with pytest.raises(ActionNotAuthorized):
        session.ask("What tool should I use to carve a cherry bowl?")

    assert controller.started == []
    assert session.history == []

    session.close()
