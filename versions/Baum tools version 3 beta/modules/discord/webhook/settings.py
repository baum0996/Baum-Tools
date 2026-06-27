from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass

from modules.discord.webhook.utils import SETTINGS_PATH, ensure_webhook_directories


@dataclass(slots=True)
class WebhookSettings:
    default_username: str = ""
    default_avatar_url: str = ""
    default_test_content: str = "BAUM TOOLS webhook test."
    request_timeout_seconds: float = 8.0
    preview_width: int = 110


class WebhookSettingsStore:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        ensure_webhook_directories()
        self.settings = self._load()

    def save(self) -> None:
        SETTINGS_PATH.write_text(
            json.dumps(asdict(self.settings), indent=2),
            encoding="utf-8",
        )

    def _load(self) -> WebhookSettings:
        if not SETTINGS_PATH.exists():
            settings = WebhookSettings()
            SETTINGS_PATH.write_text(
                json.dumps(asdict(settings), indent=2),
                encoding="utf-8",
            )
            return settings

        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Webhook settings must be a JSON object.")
            defaults = WebhookSettings()
            return WebhookSettings(
                default_username=str(
                    raw.get("default_username", defaults.default_username)
                ),
                default_avatar_url=str(
                    raw.get("default_avatar_url", defaults.default_avatar_url)
                ),
                default_test_content=str(
                    raw.get("default_test_content", defaults.default_test_content)
                ),
                request_timeout_seconds=float(
                    raw.get(
                        "request_timeout_seconds",
                        defaults.request_timeout_seconds,
                    )
                ),
                preview_width=int(raw.get("preview_width", defaults.preview_width)),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._logger.exception("Failed to load webhook settings.")
            return WebhookSettings()

