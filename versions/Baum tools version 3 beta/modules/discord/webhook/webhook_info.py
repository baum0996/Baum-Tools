from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from modules.discord.webhook.utils import discord_api_headers
from modules.discord.webhook.validation import WebhookValidator


@dataclass(slots=True)
class WebhookInfo:
    status: str
    webhook_name: str = ""
    webhook_id: str = ""
    guild_id: str = ""
    channel_id: str = ""
    avatar: str = ""
    http_status: int | None = None
    error: str = ""


class WebhookInfoClient:
    def __init__(self, validator: WebhookValidator | None = None) -> None:
        self.validator = validator or WebhookValidator()
        self._logger = logging.getLogger(__name__)

    def fetch(self, webhook_url: str, timeout: float = 8.0) -> WebhookInfo:
        if not self.validator.validate_webhook_format(webhook_url):
            return WebhookInfo(status="Invalid", error="Webhook URL format is invalid.")

        request = Request(
            webhook_url.strip(),
            headers=discord_api_headers(),
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
                return WebhookInfo(
                    status="Valid",
                    webhook_name=str(raw.get("name") or ""),
                    webhook_id=str(raw.get("id") or ""),
                    guild_id=str(raw.get("guild_id") or ""),
                    channel_id=str(raw.get("channel_id") or ""),
                    avatar=str(raw.get("avatar") or ""),
                    http_status=response.status,
                )
        except HTTPError as exc:
            return WebhookInfo(
                status="Invalid" if exc.code in {401, 403, 404} else "Unknown",
                http_status=exc.code,
                error=f"Discord returned HTTP {exc.code}.",
            )
        except (TimeoutError, URLError, OSError, json.JSONDecodeError) as exc:
            self._logger.exception("Failed to fetch webhook information.")
            return WebhookInfo(status="Unknown", error=str(exc))
