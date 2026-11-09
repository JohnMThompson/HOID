
"""SQLite persistence for HOID timers and alarms."""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc)


class SchedulerStore:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self):
        """Create the scheduler database schema."""
        self.database_path.parent.mkdir(
            parents=True, exist_ok=True
        )

        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    label TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def create_timer(self, duration_seconds, label="Timer"):
        """Create a pending timer and return its details."""
        if (
            isinstance(duration_seconds, bool)
            or not isinstance(duration_seconds, int)
            or duration_seconds < 1
            or duration_seconds > 86400
        ):
            raise ValueError(
                "Duration must be between 1 and 86400 seconds."
            )

        if not isinstance(label, str) or not label.strip():
            raise ValueError("Timer label cannot be empty.")

        now = utc_now()
        job = {
            "id": str(uuid4()),
            "kind": "timer",
            "label": label.strip(),
            "due_at": (
                now + timedelta(seconds=duration_seconds)
            ).isoformat(),
            "status": "pending",
            "created_at": now.isoformat(),
        }

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs
                    (id, kind, label, due_at, status, created_at)
                VALUES
                    (:id, :kind, :label, :due_at,
                     :status, :created_at)
                """,
                job,
            )

        return job

    def get_job(self, job_id):
        """Retrieve a job by its unique identifier."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_pending(self):
        """List pending jobs in expiration order."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM jobs
                WHERE status = 'pending'
                ORDER BY due_at ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]


    def claim_due_jobs(self, now=None, limit=10):
        """Atomically claim expired pending jobs for processing."""
        if now is None:
            now = utc_now()

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Claim timestamp must be timezone-aware.")

        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer.")

        with self._connect() as connection:
            rows = connection.execute(
                """
                UPDATE jobs
                SET status = 'processing'
                WHERE id IN (
                    SELECT id FROM jobs
                    WHERE status = 'pending'
                      AND due_at <= ?
                    ORDER BY due_at ASC
                    LIMIT ?
                )
                RETURNING *
                """,
                (now.astimezone(timezone.utc).isoformat(), limit),
            ).fetchall()

        return sorted(
            (dict(row) for row in rows),
            key=lambda job: job["due_at"],
        )
