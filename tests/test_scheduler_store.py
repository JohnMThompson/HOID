
"""Tests for HOID scheduler persistence."""

from datetime import datetime

import pytest

from hoid.scheduler_store import SchedulerStore


@pytest.fixture
def store(tmp_path):
    database = tmp_path / "scheduler.sqlite3"
    result = SchedulerStore(database)
    result.initialize()
    return result


def test_create_and_retrieve_timer(store):
    timer = store.create_timer(45, "Tea")

    saved = store.get_job(timer["id"])

    assert saved == timer
    assert saved["kind"] == "timer"
    assert saved["label"] == "Tea"
    assert saved["status"] == "pending"


def test_multiple_independent_timers(store):
    tea = store.create_timer(45, "Tea")
    laundry = store.create_timer(300, "Laundry")

    pending = store.list_pending()

    assert len(pending) == 2
    assert {job["id"] for job in pending} == {
        tea["id"],
        laundry["id"],
    }
    assert pending[0]["id"] == tea["id"]


def test_timers_survive_database_reopen(store):
    timer = store.create_timer(120, "Study")

    reopened = SchedulerStore(store.database_path)

    assert reopened.get_job(timer["id"]) == timer


def test_expiration_is_utc(store):
    timer = store.create_timer(60, "Coffee")

    due = datetime.fromisoformat(timer["due_at"])
    created = datetime.fromisoformat(timer["created_at"])

    assert due.utcoffset().total_seconds() == 0
    assert (due - created).total_seconds() == 60


@pytest.mark.parametrize(
    "duration",
    [0, -1, 86401, 1.5, True, "60"],
)
def test_invalid_durations_rejected(store, duration):
    with pytest.raises(ValueError):
        store.create_timer(duration)


@pytest.mark.parametrize("label", ["", "   ", None])
def test_invalid_labels_rejected(store, label):
    with pytest.raises(ValueError):
        store.create_timer(60, label)


def test_unknown_timer_returns_none(store):
    assert store.get_job("nonexistent") is None


def test_claim_only_expired_timers(store):
    from datetime import timedelta, timezone

    tea = store.create_timer(30, "Tea")
    laundry = store.create_timer(60, "Laundry")
    study = store.create_timer(300, "Study")

    now = datetime.now(timezone.utc) + timedelta(seconds=90)

    claimed = store.claim_due_jobs(now=now)

    assert {job["id"] for job in claimed} == {
        tea["id"],
        laundry["id"],
    }
    assert store.get_job(tea["id"])["status"] == "processing"
    assert store.get_job(laundry["id"])["status"] == "processing"
    assert store.get_job(study["id"])["status"] == "pending"


def test_expired_timer_cannot_be_claimed_twice(store):
    from datetime import timedelta, timezone

    timer = store.create_timer(30, "Coffee")
    now = datetime.now(timezone.utc) + timedelta(seconds=60)

    first = store.claim_due_jobs(now=now)
    second = store.claim_due_jobs(now=now)

    assert len(first) == 1
    assert first[0]["id"] == timer["id"]
    assert second == []


def test_claim_respects_batch_limit(store):
    from datetime import timedelta, timezone

    for index in range(5):
        store.create_timer(30, f"Timer {index}")

    now = datetime.now(timezone.utc) + timedelta(seconds=60)

    first = store.claim_due_jobs(now=now, limit=2)
    second = store.claim_due_jobs(now=now, limit=2)
    third = store.claim_due_jobs(now=now, limit=2)

    assert len(first) == 2
    assert len(second) == 2
    assert len(third) == 1
    assert store.list_pending() == []


def test_claim_rejects_invalid_inputs(store):
    from datetime import timedelta

    with pytest.raises(ValueError):
        store.claim_due_jobs(now=datetime.now())

    for limit in (0, -1, True, 1.5):
        with pytest.raises(ValueError):
            store.claim_due_jobs(limit=limit)
