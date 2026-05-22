from __future__ import annotations

import json
import mimetypes
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from automation_pcaps.config import Config
from automation_pcaps.health import check_paths, postgres_health
from automation_pcaps.pipeline import Pipeline
from automation_pcaps.state import StateStore


WEB_DIR = Path(__file__).parent / "web"


class WebHandler(BaseHTTPRequestHandler):
    server: "AutomationServer"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self._file(WEB_DIR / "index.html", "text/html; charset=utf-8")
        elif parsed.path.startswith("/static/"):
            rel = parsed.path.removeprefix("/static/")
            self._file(WEB_DIR / "static" / rel)
        elif parsed.path == "/api/status":
            self._json(self.server.pipeline.status())
        elif parsed.path == "/api/health":
            self._json({"data": self.server.health()})
        elif parsed.path == "/api/jobs":
            self._json({"data": self.server.store.list_jobs()})
        elif parsed.path == "/api/logs":
            params = urllib.parse.parse_qs(parsed.query)
            dataset_id = params.get("dataset_id", [None])[0]
            self._json({"data": self.server.store.list_logs(dataset_id=dataset_id)})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/start":
            self.server.pipeline.start()
            self._json({"ok": True})
        elif parsed.path == "/api/stop":
            self.server.pipeline.stop()
            self._json({"ok": True})
        elif parsed.path == "/api/scan":
            self.server.pipeline.start()
            self.server.pipeline.wake_once()
            self._json({"ok": True})
        elif parsed.path == "/api/credentials":
            body = self._body()
            user = str(body.get("user") or "").strip()
            password = str(body.get("password") or "")
            if not user or not password:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing user or password")
                return
            self.server.pipeline.set_credentials(user, password)
            self.server.pipeline.start()
            self.server.pipeline.wake_once()
            self._json({"ok": True})
        elif parsed.path == "/api/retry":
            dataset_id = self._body()["dataset_id"]
            self.server.store.retry_job(dataset_id)
            self.server.pipeline.start()
            self.server.pipeline.wake_once()
            self._json({"ok": True})
        elif parsed.path == "/api/retry-postgres":
            dataset_id = self._body()["dataset_id"]
            self.server.store.retry_postgres(dataset_id)
            self.server.pipeline.start()
            self.server.pipeline.wake_once()
            self._json({"ok": True})
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def _json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class AutomationServer(ThreadingHTTPServer):
    def __init__(self, cfg: Config, store: StateStore, pipeline: Pipeline) -> None:
        super().__init__((cfg.host, cfg.port), WebHandler)
        self.cfg = cfg
        self.store = store
        self.pipeline = pipeline

    def health(self) -> list[dict[str, str]]:
        checks = check_paths(self.cfg)
        checks.append({"name": "api_credentials", "status": "ok" if self.pipeline.api.has_credentials() else "warning", "detail": "set" if self.pipeline.api.has_credentials() else "pending"})
        if self.cfg.ingest_to_postgres:
            checks.append(postgres_health(self.cfg))
        return checks

