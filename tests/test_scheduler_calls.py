
"""Tests for HOID scheduler Asterisk call files."""

from uuid import uuid4

import pytest

from hoid.scheduler_calls import build_call_file, write_call_file


def test_call_file_contains_expected_settings():
    job_id = uuid4()

    content = build_call_file(job_id)

    assert "Channel: PJSIP/101\n" in content
    assert 'CallerID: "HOID" <200>\n' in content
    assert "WaitTime: 20\n" in content
    assert "RetryTime: 20\n" in content
    assert "MaxRetries: 1\n" in content
    assert "Context: internal\n" in content
    assert "Extension: 204\n" in content
    assert "Priority: 1\n" in content
    assert f"Setvar: HOID_JOB_ID={job_id}\n" in content
    assert "Archive: yes\n" in content


def test_write_call_file_to_staging(tmp_path):
    job_id = uuid4()
    staging = tmp_path / "staging"

    destination = write_call_file(job_id, staging)

    assert destination.exists()
    assert destination.name == f"hoid-{job_id}.call"
    assert destination.parent == staging
    assert f"HOID_JOB_ID={job_id}" in destination.read_text()


def test_duplicate_call_file_is_rejected(tmp_path):
    job_id = uuid4()

    write_call_file(job_id, tmp_path)

    with pytest.raises(FileExistsError):
        write_call_file(job_id, tmp_path)


@pytest.mark.parametrize(
    "job_id",
    ["not-a-uuid", "../other-file", "", None],
)
def test_invalid_job_ids_rejected(job_id):
    with pytest.raises((ValueError, TypeError, AttributeError)):
        build_call_file(job_id)


@pytest.mark.parametrize("extension", ["abc", "204\nHangup()", ""])
def test_invalid_extensions_rejected(extension):
    with pytest.raises(ValueError):
        build_call_file(uuid4(), extension=extension)
