from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from automation_pcaps.config import Config
from automation_pcaps.naming import infer_vendor_from_capture_name
from automation_pcaps.state import StateStore


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def session_dir_for(cfg: Config, filename: str) -> Path:
    stem = Path(filename).stem
    session_name = stem.split("_", 1)[0]
    vendor = infer_vendor_from_capture_name(filename)
    return cfg.workspace_dir / "out" / vendor / "sessions" / session_name


def pcap2db_command(cfg: Config, pcap_filename: str) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pcap2db",
        "run",
        "--workspace",
        str(cfg.workspace_dir),
        "--in",
        pcap_filename,
        "--filter",
        cfg.display_filter,
        "--tshark",
        cfg.tshark_path,
    ]
    if cfg.max_events is not None:
        command.extend(["--max-events", str(cfg.max_events)])
    if cfg.strict:
        command.append("--strict")
    return command


def ndjson2pg_command(cfg: Config, session_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(cfg.ndjson2pg_repo_dir / "ndjson2pg.py"),
        "--session-dir",
        str(session_dir),
    ]
    if cfg.postgres_schema:
        command.extend(["--schema", cfg.postgres_schema])
    return command


def run_logged_command(
    store: StateStore,
    dataset_id: str,
    command: list[str],
    cwd: Path,
    extra_pythonpath: Path | None = None,
) -> None:
    env = os.environ.copy()
    if extra_pythonpath:
        extra_pythonpath = extra_pythonpath.resolve()
        current = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(extra_pythonpath) if not current else f"{extra_pythonpath}{os.pathsep}{current}"
    store.add_log(dataset_id, "INFO", "Command: " + " ".join(command))
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    for line in process.stdout:
        store.add_log(dataset_id, "INFO", line.rstrip())
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Command failed with exit code {return_code}: {' '.join(command)}")
