
"""Tests for personalized scheduler announcements."""

import pytest

from hoid.scheduler_announcements import AnnouncementSelector


@pytest.fixture
def selector():
    return AnnouncementSelector()


def test_labeled_timer_uses_label(selector):
    for _ in range(20):
        message = selector.select("timer", "Tea")
        assert "Tea" in message
        assert "{label}" not in message


def test_unlabeled_timer(selector):
    for label in (None, "", "   ", "Timer"):
        message = selector.select("timer", label)
        assert message
        assert "{label}" not in message
        assert "Timer timer" not in message


def test_alarm_uses_label(selector):
    for _ in range(20):
        message = selector.select("alarm", "Meeting")
        assert "Meeting" in message
        assert "{label}" not in message


def test_unlabeled_alarm(selector):
    for label in (None, "", "Alarm"):
        message = selector.select("alarm", label)
        assert message
        assert "{label}" not in message


def test_no_immediate_template_repetition(selector):
    previous = None

    for _ in range(100):
        message = selector.select("timer", "Tea")
        assert message != previous
        previous = message


@pytest.mark.parametrize("kind", ["reminder", "", None])
def test_unsupported_job_kind(selector, kind):
    with pytest.raises(ValueError):
        selector.select(kind)


def test_label_whitespace_is_trimmed(selector):
    message = selector.select("timer", "  Coffee  ")
    assert "Coffee" in message
    assert "  Coffee  " not in message
