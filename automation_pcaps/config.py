from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    api_base_url: str
    api_user_env: str
    api_password_env: str
    poll_interval_seconds: int
    workspace_dir: Path
    pcap2db_repo_dir: Path
    ndjson2pg_repo_dir: Path
    state_db_path: Path
    tshark_path: str
    display_filter: str
    dataset_title_keywords: tuple[str, ...]
    auto_normalize_capture_filenames: bool
    default_station_id: int
    default_device_type: str
    filename_overrides: dict[str, str]
    max_events: int | None
    strict: bool
    ingest_to_postgres: bool
    postgres_schema: str | None
    host: str
    port: int

    @property
    def raw_dir(self) -> Path:
        return self.workspace_dir / "pcaps" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.workspace_dir / "pcaps" / "processed"

    @property
    def out_dir(self) -> Path:
        return self.workspace_dir / "out"

    @property
    def ndjson_env_path(self) -> Path:
        return self.ndjson2pg_repo_dir / ".env"


def load_config(path: Path) -> Config:
    path = path.expanduser().resolve()
    repo_root = path.parent.parent

    def resolve_repo_path(value: str) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_absolute():
            return candidate
        return repo_root / candidate

    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)

    return Config(
        api_base_url=str(data["api_base_url"]).rstrip("/"),
        api_user_env=str(data.get("api_user_env", "DS4MOVEUS_USER")),
        api_password_env=str(data.get("api_password_env", "DS4MOVEUS_PASSWORD")),
        poll_interval_seconds=int(data.get("poll_interval_seconds", 60)),
        workspace_dir=Path(data["workspace_dir"]).expanduser(),
        pcap2db_repo_dir=resolve_repo_path(str(data["pcap2db_repo_dir"])),
        ndjson2pg_repo_dir=resolve_repo_path(str(data["ndjson2pg_repo_dir"])),
        state_db_path=Path(data["state_db_path"]).expanduser(),
        tshark_path=str(data.get("tshark_path", "tshark")),
        display_filter=str(data.get("display_filter", "its")),
        dataset_title_keywords=tuple(str(v).lower() for v in data.get("dataset_title_keywords", [])),
        auto_normalize_capture_filenames=bool(data.get("auto_normalize_capture_filenames", True)),
        default_station_id=int(data.get("default_station_id", 1001)),
        default_device_type=str(data.get("default_device_type", "obu")).lower(),
        filename_overrides={str(k): str(v) for k, v in data.get("filename_overrides", {}).items()},
        max_events=data.get("max_events"),
        strict=bool(data.get("strict", False)),
        ingest_to_postgres=bool(data.get("ingest_to_postgres", True)),
        postgres_schema=data.get("postgres_schema"),
        host=str(data.get("host", "127.0.0.1")),
        port=int(data.get("port", 8088)),
    )


def ensure_dirs(cfg: Config) -> None:
    cfg.raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
