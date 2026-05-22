from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from automation_pcaps.config import Config


class ApiClient:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.token: str | None = None
        self.user: str | None = None
        self.password: str | None = None

    def set_credentials(self, user: str, password: str) -> None:
        self.user = user
        self.password = password
        self.token = None

    def has_credentials(self) -> bool:
        user, password = self._credential_values()
        return bool(user and password)

    def login(self) -> None:
        user, password = self._credential_values()
        if not user or not password:
            raise RuntimeError(f"Missing API credentials in {self.cfg.api_user_env} and {self.cfg.api_password_env}")
        response = self._json_request("POST", "/auth/login", body={"user": user, "password": password}, auth=False)
        self.token = response["access_token"]

    def list_available_datasets(self) -> list[dict[str, Any]]:
        response = self._json_request("GET", "/datasets/available")
        return list(response.get("data", []))

    def download_dataset(self, artifact_url: str, destination: Path) -> None:
        query = urllib.parse.urlencode({"url_artifact": artifact_url})
        url = f"{self.cfg.api_base_url}/datasets/download?{query}"
        request = urllib.request.Request(url, method="GET", headers=self._headers())
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content_type = response.headers.get("Content-Type", "")
                payload = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Download failed: HTTP {exc.code} {detail}") from exc

        if "application/json" in content_type:
            self._write_from_download_json(payload, destination)
            return
        destination.write_bytes(payload)

    def _write_from_download_json(self, payload: bytes, destination: Path) -> None:
        data = json.loads(payload.decode("utf-8"))
        for key in ("content", "data", "file"):
            value = data.get(key)
            if isinstance(value, str):
                destination.write_bytes(value.encode("latin-1"))
                return
        for key in ("url", "download_url", "href"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                request = urllib.request.Request(value, method="GET", headers=self._headers())
                with urllib.request.urlopen(request, timeout=120) as response:
                    destination.write_bytes(response.read())
                return
        if "error" in data:
            raise RuntimeError(f"Download API returned error: {data['error']}")
        raise RuntimeError(f"Unsupported download JSON response keys: {', '.join(data.keys())}")

    def _json_request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        data: bytes | None = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if auth:
            headers.update(self._headers())
        request = urllib.request.Request(f"{self.cfg.api_base_url}{path}", data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API {method} {path} failed: {exc.code} {detail}") from exc

    def _headers(self) -> dict[str, str]:
        if not self.token:
            self.login()
        return {"Authorization": f"Bearer {self.token}"}

    def _credential_values(self) -> tuple[str | None, str | None]:
        return self.user or os.environ.get(self.cfg.api_user_env), self.password or os.environ.get(
            self.cfg.api_password_env
        )

