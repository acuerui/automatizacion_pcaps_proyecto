from __future__ import annotations

import queue
import sqlite3
import threading

from automation_pcaps.api_client import ApiClient
from automation_pcaps.commands import (
    file_sha256,
    ndjson2pg_command,
    pcap2db_command,
    run_logged_command,
    session_dir_for,
)
from automation_pcaps.config import Config
from automation_pcaps.naming import filename_for_dataset
from automation_pcaps.state import StateStore


class Pipeline:
    def __init__(self, cfg: Config, store: StateStore) -> None:
        self.cfg = cfg
        self.store = store
        self.api = ApiClient(cfg)
        self._stop = threading.Event()
        self._wakeup: queue.Queue[None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._worker_enabled = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._worker_enabled = True
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._loop, name="pcap-worker", daemon=True)
                self._thread.start()
        self.wake_once()

    def stop(self) -> None:
        with self._lock:
            self._worker_enabled = False

    def shutdown(self) -> None:
        self._stop.set()
        self.wake_once()

    def wake_once(self) -> None:
        try:
            self._wakeup.put_nowait(None)
        except queue.Full:
            pass

    def set_credentials(self, user: str, password: str) -> None:
        self.api.set_credentials(user, password)
        self.store.add_log(None, "INFO", "API credentials updated from web UI")

    def status(self) -> dict[str, object]:
        return {
            "worker_enabled": self._worker_enabled,
            "thread_alive": self._thread is not None and self._thread.is_alive(),
            "has_credentials": self.api.has_credentials(),
            "poll_interval_seconds": self.cfg.poll_interval_seconds,
            "workspace_dir": str(self.cfg.workspace_dir),
            "ingest_to_postgres": self.cfg.ingest_to_postgres,
        }

    def _loop(self) -> None:
        self.store.add_log(None, "INFO", "Worker thread started")
        while not self._stop.is_set():
            if self._worker_enabled:
                try:
                    self.scan_once()
                    self.process_pending_once()
                except Exception as exc:
                    self.store.add_log(None, "ERROR", str(exc))
            try:
                self._wakeup.get(timeout=self.cfg.poll_interval_seconds)
            except queue.Empty:
                pass

    def scan_once(self) -> None:
        if not self.api.has_credentials():
            self.store.add_log(None, "WARNING", "Waiting for API credentials")
            return
        datasets = self.api.list_available_datasets()
        new_count = 0
        skipped_count = 0
        for dataset in datasets:
            filename = filename_for_dataset(dataset, self.cfg)
            if filename is None:
                skipped_count += 1
                continue
            if self.store.upsert_detected(dataset, filename):
                new_count += 1
        self.store.add_log(
            None,
            "INFO",
            f"Scan completed. {new_count} new dataset(s), {skipped_count} skipped, {len(datasets)} total.",
        )

    def process_pending_once(self) -> None:
        while self._worker_enabled:
            job = self.store.next_pending_job()
            if job is None:
                return
            self.process_job(job)

    def process_job(self, job: sqlite3.Row) -> None:
        dataset_id = str(job["dataset_id"])
        try:
            if job["status"] == "detected":
                self._download(job)
                job = self._get_job(dataset_id)
            if job["status"] == "downloaded":
                self._transform(job)
                job = self._get_job(dataset_id)
            if job["status"] == "transformed" and self.cfg.ingest_to_postgres:
                self._load_postgres(job)
            elif job["status"] == "transformed":
                self.store.set_status(dataset_id, "loaded", "Postgres ingestion disabled; job finished after transform")
        except Exception as exc:
            self.store.set_status(dataset_id, "failed", str(exc), error=str(exc))

    def _download(self, job: sqlite3.Row) -> None:
        dataset_id = str(job["dataset_id"])
        destination = self.cfg.raw_dir / str(job["filename"])
        temp_destination = destination.with_name(f".{destination.name}.download")
        if temp_destination.exists():
            temp_destination.unlink()
        self.store.set_status(dataset_id, "downloading", f"Downloading to {destination}")
        self.api.download_dataset(str(job["artifact_url"]), temp_destination)
        temp_destination.replace(destination)
        self.store.set_status(
            dataset_id,
            "downloaded",
            f"Downloaded {destination.name}",
            downloaded_path=str(destination),
            sha256=file_sha256(destination),
        )

    def _transform(self, job: sqlite3.Row) -> None:
        dataset_id = str(job["dataset_id"])
        downloaded_path = sqlite_path(job["downloaded_path"])
        self.store.set_status(dataset_id, "transforming", f"Running pcap2db for {downloaded_path.name}")
        run_logged_command(
            self.store,
            dataset_id,
            pcap2db_command(self.cfg, downloaded_path.name),
            cwd=self.cfg.pcap2db_repo_dir,
            extra_pythonpath=self.cfg.pcap2db_repo_dir / "src",
        )
        session_dir = session_dir_for(self.cfg, downloaded_path.name)
        self.store.set_status(dataset_id, "transformed", f"Transform completed: {session_dir}", session_dir=str(session_dir))

    def _load_postgres(self, job: sqlite3.Row) -> None:
        dataset_id = str(job["dataset_id"])
        session_dir = sqlite_path(job["session_dir"])
        self.store.set_status(dataset_id, "loading_pg", f"Loading Postgres from {session_dir}")
        run_logged_command(
            self.store,
            dataset_id,
            ndjson2pg_command(self.cfg, session_dir),
            cwd=self.cfg.ndjson2pg_repo_dir,
        )
        self.store.set_status(dataset_id, "loaded", "Postgres load completed")

    def _get_job(self, dataset_id: str) -> sqlite3.Row:
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE dataset_id = ?", (dataset_id,)).fetchone()
        if row is None:
            raise RuntimeError(f"Job disappeared: {dataset_id}")
        return row


def sqlite_path(value: object) -> "Path":
    from pathlib import Path

    if value is None:
        raise RuntimeError("Expected path value, got NULL")
    return Path(str(value))

