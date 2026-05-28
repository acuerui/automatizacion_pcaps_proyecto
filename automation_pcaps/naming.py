from __future__ import annotations

import contextlib
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from automation_pcaps.config import Config


def filename_for_dataset(dataset: dict[str, Any], cfg: Config) -> str | None:
    dataset_id = str(dataset.get("id") or "")
    title = str(dataset.get("title") or "")
    searchable_text = dataset_searchable_text(dataset)
    looks_like_pcap = dataset_looks_like_capture(dataset, searchable_text)
    if not looks_like_pcap:
        return None
    if cfg.dataset_title_keywords and not any(keyword in searchable_text for keyword in cfg.dataset_title_keywords):
        standard_name = best_dataset_filename(dataset)
        if not looks_like_standard_capture(standard_name):
            return None

    override = cfg.filename_overrides.get(title) or cfg.filename_overrides.get(dataset_id)
    if override:
        return safe_pcap_filename(override, dataset_id)

    filename = best_dataset_filename(dataset)
    if looks_like_standard_capture(filename):
        return safe_pcap_filename(filename, dataset_id)

    if cfg.auto_normalize_capture_filenames:
        return build_normalized_capture_filename(dataset, cfg)

    if filename.lower().endswith((".pcap", ".pcapng")):
        return safe_pcap_filename(filename, dataset_id)

    return None


def dataset_looks_like_capture(dataset: dict[str, Any], searchable_text: str) -> bool:
    filename = best_dataset_filename(dataset)
    media_type = str(dataset.get("mediaType") or dataset.get("media_type") or "").lower()
    extension = str(dataset.get("extension") or "").lower().lstrip(".")
    return (
        "pcap" in media_type
        or extension in {"pcap", "pcapng"}
        or filename.lower().endswith((".pcap", ".pcapng"))
        or looks_like_standard_capture(filename)
        or "pcap" in searchable_text
        or "pcapng" in searchable_text
    )


def dataset_searchable_text(dataset: dict[str, Any]) -> str:
    values: list[str] = []
    for key in (
        "id",
        "title",
        "description",
        "mediaType",
        "media_type",
        "schema",
        "extension",
        "file_name",
        "filename",
        "name",
    ):
        value = dataset.get(key)
        if value is not None:
            values.append(str(value))
    subcategories = dataset.get("subcategories")
    if isinstance(subcategories, list):
        values.extend(str(value) for value in subcategories)
    return " ".join(values).lower()


def best_dataset_filename(dataset: dict[str, Any]) -> str:
    candidates = [
        dataset.get("file_name"),
        dataset.get("filename"),
        dataset.get("name"),
        dataset.get("title"),
        Path(urllib.parse.urlparse(str(dataset.get("id") or "")).path).name,
    ]
    for candidate in candidates:
        if candidate and str(candidate).lower().endswith((".pcap", ".pcapng")):
            return Path(str(candidate)).name.strip()
    for candidate in candidates:
        if candidate:
            return Path(str(candidate)).name.strip()
    return "capture.pcap"


def safe_pcap_filename(title: str, fallback: str) -> str:
    candidate = Path(title).name.strip()
    if not candidate.lower().endswith((".pcap", ".pcapng")):
        fallback_name = Path(urllib.parse.urlparse(fallback).path).name
        candidate = fallback_name if fallback_name.lower().endswith((".pcap", ".pcapng")) else f"{candidate}.pcap"
    return "".join(ch for ch in candidate if ch not in '<>:"/\\|?*').strip() or "capture.pcap"


STANDARD_CAPTURE_RE = re.compile(
    r"^(?P<timestamp>\d{8}T\d{6}Z)_"
    r"(?P<vendor>cohda|kapsch|swarco)_"
    r"(?P<device_type>rsu|obu)_"
    r"(?P<station_id>\d+)"
    r"(?:_(?P<direction>tx|rx))?"
    r"(?:\.pcap(?:ng)?)?$",
    re.IGNORECASE,
)


def looks_like_standard_capture(filename: str) -> bool:
    match = STANDARD_CAPTURE_RE.match(Path(filename).name.strip())
    if not match:
        return False
    vendor = match.group("vendor").lower()
    direction = match.group("direction")
    if vendor == "kapsch":
        return direction is None
    return direction is not None


def build_normalized_capture_filename(dataset: dict[str, Any], cfg: Config) -> str:
    title = str(dataset.get("title") or "capture")
    lower_title = title.lower()
    vendor = infer_vendor_from_text(lower_title)
    direction = infer_direction_from_text(lower_title)
    timestamp = timestamp_from_dataset(dataset)
    device_type = infer_device_type_from_text(lower_title) or cfg.default_device_type
    station_id = infer_station_id_from_text(lower_title) or cfg.default_station_id

    if vendor == "kapsch":
        return f"{timestamp}_{vendor}_{device_type}_{station_id}.pcap"
    return f"{timestamp}_{vendor}_{device_type}_{station_id}_{direction}.pcap"


def infer_vendor_from_text(text: str) -> str:
    if "cohda" in text:
        return "cohda"
    if "kapsch" in text:
        return "kapsch"
    if "swarco" in text:
        return "swarco"
    if "lacroix" in text:
        return "swarco"
    return "cohda"


def infer_direction_from_text(text: str) -> str:
    if re.search(r"(^|[_\W])tx([_\W]|$)", text):
        return "tx"
    return "rx"


def infer_device_type_from_text(text: str) -> str | None:
    if "rsu" in text:
        return "rsu"
    if "obu" in text:
        return "obu"
    return None


def infer_station_id_from_text(text: str) -> int | None:
    match = STANDARD_CAPTURE_RE.match(Path(text).name.strip())
    if match:
        return int(match.group("station_id"))
    for match in re.finditer(r"(?<!\d)(\d{4,})(?!\d)", text):
        value = match.group(1)
        if re.fullmatch(r"\d{8}", value):
            continue
        return int(value)
    return None


def timestamp_from_dataset(dataset: dict[str, Any]) -> str:
    title = str(dataset.get("title") or "")
    match = re.search(r"\d{8}T\d{6}Z", title)
    if match:
        return match.group(0)
    raw = str(dataset.get("creation_date") or dataset.get("modification_date") or "")
    if raw:
        with contextlib.suppress(ValueError):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def infer_vendor_from_capture_name(filename: str) -> str:
    parts = Path(filename).stem.split("_")
    if len(parts) < 2:
        raise RuntimeError(f"Cannot infer vendor from capture filename: {filename}")
    return parts[1].lower()
