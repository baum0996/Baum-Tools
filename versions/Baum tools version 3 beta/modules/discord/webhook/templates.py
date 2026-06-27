from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path

from modules.discord.webhook.utils import JsonDict, TEMPLATE_DIR, ensure_webhook_directories, unique_path
from modules.discord.webhook.validation import ValidationResult, WebhookValidator


class TemplateStore:
    def __init__(self, validator: WebhookValidator | None = None) -> None:
        self.validator = validator or WebhookValidator()
        self._logger = logging.getLogger(__name__)
        ensure_webhook_directories()

    def list_templates(self, query: str = "") -> list[Path]:
        lowered = query.casefold().strip()
        templates = sorted(TEMPLATE_DIR.glob("*.json"), key=lambda path: path.stem.casefold())
        if not lowered:
            return templates
        return [path for path in templates if lowered in path.stem.casefold()]

    def save(self, name: str, payload: JsonDict) -> Path:
        path = unique_path(TEMPLATE_DIR, name, ".json")
        serializable = deepcopy(payload)
        path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
        return path

    def load(self, path: Path) -> tuple[JsonDict | None, ValidationResult]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._logger.exception("Failed to load template.")
            return None, ValidationResult("Invalid", [str(exc)], [])

        result = self.validator.validate_import_json(raw)
        if result.errors or not isinstance(raw, dict):
            return None, result
        return raw, result

    def rename(self, path: Path, new_name: str) -> Path:
        target = unique_path(TEMPLATE_DIR, new_name, ".json")
        return path.rename(target)

    def duplicate(self, path: Path) -> Path:
        target = unique_path(TEMPLATE_DIR, f"{path.stem}_copy", ".json")
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return target

    def delete(self, path: Path) -> None:
        path.unlink()

