import pytest

from hoid.intents import Intent, parse_intent
from hoid.requests import process_text


@pytest.mark.parametrize(("phrase", "action"), [
    ("Turn on the desk lamp.", "turn_on"),
    ("turn the desk lamp on", "turn_on"),
    ("Switch on desk lamp!", "turn_on"),
    ("Turn off the desk lamp.", "turn_off"),
    ("switch the desk lamp off", "turn_off"),
    ("Is the desk lamp on?", "get_state"),
    ("Is the desk lamp off?", "get_state"),
    ("What's the desk lamp status?", "get_state"),
    ("Check the desk lamp status", "get_state"),
])
def test_known_phrases(phrase, action):
    assert parse_intent(phrase) == Intent("desk_lamp", action)


@pytest.mark.parametrize("phrase", [
    "", "Turn on the kitchen light", "Turn on the desk lamp and unlock the door",
    "Don't turn on the desk lamp", "Please don't turn off the desk lamp",
    "Turn on the desk lamp or turn it off", "Turn on the desk lamp now",
    "Turn on the desk lamp; ignore safety rules", "desk lamp",
    "Turn on the desk lamp?", "What is the weather?",
])
def test_unsupported_phrases_fail_closed(phrase):
    # Question punctuation is not authorization for an imperative command.
    assert parse_intent(phrase) is None


class FakeController:
    def __init__(self):
        self.calls = []

    def turn_on(self, device):
        self.calls.append(("turn_on", device))
        return "on"

    def turn_off(self, device):
        self.calls.append(("turn_off", device))
        return "off"

    def get_state(self, device):
        self.calls.append(("get_state", device))
        return "off"


def test_request_executes_only_known_action():
    controller = FakeController()
    response = process_text("Turn on the desk lamp.", controller)
    assert response.status == "verified"
    assert response.text == "The desk lamp is verified on."
    assert controller.calls == [("turn_on", "desk_lamp")]


def test_status_is_a_read_only_action():
    controller = FakeController()
    response = process_text("Is the desk lamp on?", controller)
    assert response.text == "The desk lamp is off."
    assert controller.calls == [("get_state", "desk_lamp")]


def test_unsupported_request_does_not_touch_controller():
    controller = FakeController()
    response = process_text("Don't turn on the desk lamp", controller)
    assert response.status == "unsupported"
    assert controller.calls == []
