from __future__ import annotations

import shutil
import socket
from pathlib import Path

from automation_pcaps.config import Config


def check_paths(cfg: Config) -> list[dict[str, str]]:
    checks = [
        ("pcap2db", cfg.pcap2db_repo_dir / "src" / "pcap2db" / "__main__.py"),
        ("ndjson2pg", cfg.ndjson2pg_repo_dir / "ndjson2pg.py"),
        ("workspace", cfg.workspace_dir),
    ]
    results = []
    for name, path in checks:
        results.append({"name": name, "status": "ok" if path.exists() else "error", "detail": str(path)})

    tshark_ok = bool(shutil.which(cfg.tshark_path)) if cfg.tshark_path == "tshark" else Path(cfg.tshark_path).exists()
    results.append({"name": "tshark", "status": "ok" if tshark_ok else "error", "detail": cfg.tshark_path})
    return results


def assert_startup_checks(cfg: Config) -> None:
    errors = [item for item in check_paths(cfg) if item["status"] == "error" and item["name"] != "workspace"]
    if errors:
        raise RuntimeError("\n".join(f"{item['name']} not ready: {item['detail']}" for item in errors))


def postgres_health(cfg: Config, timeout: float = 2.0) -> dict[str, str]:
    env = read_dotenv(cfg.ndjson_env_path)
    host = env.get("POSTGRES_HOST")
    port = int(env.get("POSTGRES_PORT") or "5432")
    missing = [key for key in ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD") if not env.get(key)]
    if missing:
        return {"name": "postgres", "status": "warning", "detail": "Missing: " + ", ".join(missing)}
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return {"name": "postgres", "status": "ok", "detail": f"{host}:{port}"}
    except OSError as exc:
        return {"name": "postgres", "status": "error", "detail": f"{host}:{port} - {exc}"}


def read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

