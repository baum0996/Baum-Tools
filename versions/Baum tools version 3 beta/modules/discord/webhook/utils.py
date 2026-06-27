from __future__ import annotations

import re
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from constants import APP_NAME, APP_VERSION, BASE_DIR


WEBHOOK_DATA_DIR = BASE_DIR / "modules" / "discord" / "webhook" / "data"
TEMPLATE_DIR = WEBHOOK_DATA_DIR / "templates"
EXPORT_DIR = WEBHOOK_DATA_DIR / "exports"
SETTINGS_PATH = WEBHOOK_DATA_DIR / "settings.json"

DISCORD_WEBHOOK_RE = re.compile(
    r"^https://(?:(?:canary|ptb)\.)?discord(?:app)?\.com/api/"
    r"(?:v\d+/)?webhooks/(?P<id>\d{17,20})/(?P<token>[\w.-]{20,})/?$"
)
HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")

JsonDict = dict[str, Any]


def discord_api_headers(content_type: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "User-Agent": f"{APP_NAME}/{APP_VERSION} DiscordWebhookModule",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def ensure_webhook_directories() -> None:
    for path in (WEBHOOK_DATA_DIR, TEMPLATE_DIR, EXPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def default_payload() -> JsonDict:
    return {
        "webhook_url": "",
        "username": "",
        "avatar_url": "",
        "content": "",
        "tts": False,
        "allowed_mentions": {"parse": []},
        "suppress_embeds": False,
        "embeds": [],
    }


def clean_payload_for_send(payload: JsonDict) -> JsonDict:
    sendable = deepcopy(payload)
    sendable.pop("webhook_url", None)
    suppress_embeds = bool(sendable.pop("suppress_embeds", False))

    if suppress_embeds:
        sendable["flags"] = int(sendable.get("flags", 0)) | 4
    elif "flags" in sendable and int(sendable["flags"]) == 0:
        sendable.pop("flags", None)

    sendable["embeds"] = [clean_embed(embed) for embed in sendable.get("embeds", [])]
    return strip_empty(sendable)


def clean_embed(embed: JsonDict) -> JsonDict:
    cleaned = deepcopy(embed)
    label = cleaned.pop("_label", None)
    if label is not None:
        cleaned["_label"] = label
    cleaned.pop("_label", None)
    return strip_empty(cleaned)


def strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {
            key: strip_empty(item)
            for key, item in value.items()
            if item is not None and item != "" and item != [] and item != {}
        }
        return cleaned
    if isinstance(value, list):
        return [
            strip_empty(item)
            for item in value
            if item is not None and item != "" and item != [] and item != {}
        ]
    return value


def normalize_hex_color(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return ""
    if not HEX_COLOR_RE.fullmatch(candidate):
        raise ValueError("HEX color must be in the form #5865F2.")
    return candidate.upper() if candidate.startswith("#") else f"#{candidate.upper()}"


def hex_to_discord_int(value: str) -> int:
    color = normalize_hex_color(value)
    return int(color[1:], 16)


def discord_int_to_hex(value: object) -> str:
    try:
        color = int(value)
    except (TypeError, ValueError):
        return ""
    if color < 0 or color > 0xFFFFFF:
        return ""
    return f"#{color:06X}"


def now_iso_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._ -]+", "_", name.strip()).strip(". ")
    return safe or "webhook_payload"


def unique_path(directory: Path, stem: str, suffix: str) -> Path:
    path = directory / f"{safe_filename(stem)}{suffix}"
    index = 2
    while path.exists():
        path = directory / f"{safe_filename(stem)}_{index}{suffix}"
        index += 1
    return path
