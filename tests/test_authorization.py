import pytest

from hoid.authorization import (
    ActionNotAuthorized,
    authorize_action,
)


@pytest.mark.parametrize(
    "user_text",
    [
        "Set a timer for 30 seconds.",
        "Start a timer for five minutes.",
        "Ring me in 10 minutes.",
        "Remind me in twenty minutes.",
        "Give me thirty seconds and then ring me.",
    ],
)
def test_explicit_timer_requests_authorized(user_text):
    authorize_action(user_text, "start_timer")


@pytest.mark.parametrize(
    "user_text",
    [
        "What tool should I use for carving?",
        "What is a timer?",
        "How do I build a timer?",
        "Tell me about cherry wood.",
        "Set a timer.",
        "Make that ten minutes.",
    ],
)
def test_unrelated_or_incomplete_requests_rejected(user_text):
    with pytest.raises(ActionNotAuthorized):
        authorize_action(user_text, "start_timer")


def test_unknown_capability_rejected():
    with pytest.raises(ActionNotAuthorized):
        authorize_action(
            "Turn on the office lamp.",
            "turn_on_light",
        )


@pytest.mark.parametrize(
    "user_text",
    [
        "Don't start a timer for ten minutes.",
        "Do not set a timer for 30 seconds.",
        "Please don't ring me in five minutes.",
        "I don't want you to remind me in twenty minutes.",
        "Can you explain how to set a timer for ten minutes?",
        "What happens if I ask you to ring me in five minutes?",
    ],
)
def test_non_action_requests_are_not_authorized(user_text):
    with pytest.raises(ActionNotAuthorized):
        authorize_action(user_text, "start_timer")
