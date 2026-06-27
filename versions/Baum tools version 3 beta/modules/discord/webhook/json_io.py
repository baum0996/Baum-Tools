from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from modules.discord.webhook.utils import JsonDict
from modules.discord.webhook.validation import ValidationResult, WebhookValidator


class WebhookJsonIO:
    def __init__(self, validator: WebhookValidator | None = None) -> None:
        self.validator = validator or WebhookValidator()
        self._logger = logging.getLogger(__name__)

    def import_from_file(self, path: Path) -> tuple[JsonDict | None, ValidationResult]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._logger.exception("Failed to import webhook JSON.")
            return None, ValidationResult("Invalid", [str(exc)], [])

        result = self.validator.validate_import_json(raw)
        if not result.errors and isinstance(raw, dict):
            return self._normalize_import(raw), result
        return None, result

    def export_to_file(self, path: Path, payload: JsonDict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_pretty_json(payload), encoding="utf-8")

    @staticmethod
    def to_pretty_json(payload: JsonDict) -> str:
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @staticmethod
    def _normalize_import(raw: dict[str, Any]) -> JsonDict:
        payload = dict(raw)
        payload.setdefault("webhook_url", "")
        payload.setdefault("username", "")
        payload.setdefault("avatar_url", "")
        payload.setdefault("content", "")
        payload.setdefault("tts", False)
        payload.setdefault("allowed_mentions", {"parse": []})
        payload.setdefault("suppress_embeds", bool(int(payload.get("flags", 0)) & 4))
        payload.setdefault("embeds", [])
        return payload

