from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

from automation_pcaps.time_utils import utc_now


STATUSES = (
    "detected",
    "downloading",
    "downloaded",
    "transforming",
    "transformed",
    "loading_pg",
    "loaded",
    "failed",
)


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    dataset_id TEXT PRIMARY KEY,
                    title TEXT,
                    artifact_url TEXT,
                    filename TEXT,
                    status TEXT NOT NULL,
                    media_type TEXT,
                    created_at TEXT,
                    modified_at TEXT,
                    detected_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    downloaded_path TEXT,
                    session_dir TEXT,
                    sha256 TEXT,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    ts TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                """
            )

    def upsert_detected(self, dataset: dict[str, Any], filename: str) -> bool:
        dataset_id = str(dataset.get("id") or dataset.get("url") or dataset.get("title"))
        title = str(dataset.get("title") or dataset_id)
        now = utc_now()
        with self._lock, self.connect() as conn:
            exists = conn.execute("SELECT 1 FROM jobs WHERE dataset_id = ?", (dataset_id,)).fetchone()
            if exists:
                return False
            conn.execute(
                """
                INSERT INTO jobs (
                    dataset_id, title, artifact_url, filename, status, media_type,
                    created_at, modified_at, detected_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dataset_id,
                    title,
                    dataset_id,
                    filename,
                    "detected",
                    dataset.get("mediaType") or dataset.get("media_type"),
                    dataset.get("creation_date"),
                    dataset.get("modification_date"),
                    now,
                    now,
                ),
            )
            conn.execute(
                "INSERT INTO logs (dataset_id, ts, level, message) VALUES (?, ?, ?, ?)",
                (dataset_id, now, "INFO", f"Dataset detected: {title}"),
            )
            return True

    def next_pending_job(self) -> sqlite3.Row | None:
        with self._lock, self.connect() as conn:
            return conn.execute(
                """
                SELECT * FROM jobs
                WHERE status IN ('detected', 'downloaded', 'transformed')
                ORDER BY detected_at ASC
                LIMIT 1
                """
            ).fetchone()

    def set_status(self, dataset_id: str, status: str, message: str | None = None, **fields: Any) -> None:
        if status not in STATUSES:
            raise ValueError(f"Unknown status: {status}")
        now = utc_now()
        assignments = ["status = ?", "updated_at = ?"]
        values: list[Any] = [status, now]
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            values.append(value)
        values.append(dataset_id)
        with self._lock, self.connect() as conn:
            conn.execute(f"UPDATE jobs SET {', '.join(assignments)} WHERE dataset_id = ?", values)
            if message:
                conn.execute(
                    "INSERT INTO logs (dataset_id, ts, level, message) VALUES (?, ?, ?, ?)",
                    (dataset_id, now, "INFO" if status != "failed" else "ERROR", message),
                )

    def add_log(self, dataset_id: str | None, level: str, message: str) -> None:
        with self._lock, self.connect() as conn:
            conn.execute(
                "INSERT INTO logs (dataset_id, ts, level, message) VALUES (?, ?, ?, ?)",
                (dataset_id, utc_now(), level, message),
            )

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock, self.connect() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY detected_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def list_logs(self, dataset_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        with self._lock, self.connect() as conn:
            if dataset_id:
                rows = conn.execute(
                    "SELECT * FROM logs WHERE dataset_id = ? ORDER BY id DESC LIMIT ?",
                    (dataset_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def retry_job(self, dataset_id: str) -> None:
        self.set_status(dataset_id, "detected", "Retry requested", error=None)

    def retry_postgres(self, dataset_id: str) -> None:
        self.set_status(dataset_id, "transformed", "Postgres retry requested", error=None)

