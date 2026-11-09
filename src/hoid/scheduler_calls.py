
"""Create outbound Asterisk call files for HOID notifications."""

from pathlib import Path
from uuid import UUID


def build_call_file(job_id, extension="204"):
    """Return an Asterisk call file for a scheduler job."""
    job_id = str(UUID(str(job_id)))

    if not extension.isdigit():
        raise ValueError("Extension must be numeric.")

    return (
        "Channel: PJSIP/101\n"
        'CallerID: "HOID" <200>\n'
        "WaitTime: 20\n"
        "RetryTime: 20\n"
        "MaxRetries: 1\n"
        "Context: internal\n"
        f"Extension: {extension}\n"
        "Priority: 1\n"
        f"Setvar: HOID_JOB_ID={job_id}\n"
        "Archive: yes\n"
    )


def write_call_file(job_id, staging_directory):
    """Write a complete call file without submitting it."""
    job_id = str(UUID(str(job_id)))
    staging_directory = Path(staging_directory)
    staging_directory.mkdir(parents=True, exist_ok=True)

    destination = staging_directory / f"hoid-{job_id}.call"
    content = build_call_file(job_id)

    with destination.open("x", encoding="utf-8") as file:
        file.write(content)

    return destination
