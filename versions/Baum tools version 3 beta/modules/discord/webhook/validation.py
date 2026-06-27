from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from modules.discord.webhook.utils import (
    DISCORD_WEBHOOK_RE,
    HEX_COLOR_RE,
    JsonDict,
    clean_payload_for_send,
    discord_api_headers,
)


@dataclass(slots=True)
class ValidationResult:
    status: str
    errors: list[str]
    warnings: list[str]
    http_status: int | None = None
    response_text: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "Valid" and not self.errors


class WebhookValidator:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def validate_payload(self, payload: JsonDict) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(payload, dict):
            return ValidationResult("Invalid", ["Payload must be a JSON object."], [])

        webhook_url = str(payload.get("webhook_url", "")).strip()
        if webhook_url and not self.validate_webhook_format(webhook_url):
            errors.append("Webhook URL format is invalid.")

        content = str(payload.get("content", ""))
        embeds = payload.get("embeds", [])
        if not content and not embeds:
            warnings.append("Payload has no content or embeds.")
        if len(content) > 2000:
            errors.append("Content exceeds Discord's 2000 character limit.")
        if not isinstance(embeds, list):
            errors.append("Embeds must be a list.")
            embeds = []
        if len(embeds) > 10:
            errors.append("Discord allows at most 10 embeds per webhook message.")

        for index, embed in enumerate(embeds, start=1):
            self._validate_embed(index, embed, errors)

        try:
            encoded = json.dumps(clean_payload_for_send(payload)).encode("utf-8")
        except (TypeError, ValueError) as exc:
            errors.append(f"Payload cannot be serialized: {exc}")
        else:
            if len(encoded) > 600_000:
                warnings.append("Payload is unusually large and may be rejected.")

        return ValidationResult("Invalid" if errors else "Valid", errors, warnings)

    def validate_import_json(self, data: Any) -> ValidationResult:
        if not isinstance(data, dict):
            return ValidationResult("Invalid", ["Imported JSON must be an object."], [])
        return self.validate_payload(data)

    def validate_webhook_format(self, webhook_url: str) -> bool:
        return DISCORD_WEBHOOK_RE.fullmatch(webhook_url.strip()) is not None

    def validate_webhook_url(self, webhook_url: str, timeout: float = 8.0) -> ValidationResult:
        if not self.validate_webhook_format(webhook_url):
            return ValidationResult("Invalid", ["Webhook URL format is invalid."], [])

        request = Request(
            webhook_url.strip(),
            headers=discord_api_headers(),
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read(4096).decode("utf-8", errors="replace")
                return ValidationResult(
                    "Valid",
                    [],
                    [],
                    http_status=response.status,
                    response_text=body,
                )
        except HTTPError as exc:
            body = exc.read(4096).decode("utf-8", errors="replace")
            status = "Invalid" if exc.code in {401, 403, 404} else "Unknown"
            return ValidationResult(
                status,
                [f"Discord returned HTTP {exc.code}."],
                [],
                http_status=exc.code,
                response_text=body,
            )
        except (TimeoutError, URLError, OSError) as exc:
            self._logger.exception("Webhook reachability check failed.")
            return ValidationResult("Unknown", [str(exc)], [])

    def _validate_embed(self, index: int, embed: object, errors: list[str]) -> None:
        if not isinstance(embed, dict):
            errors.append(f"Embed {index} must be an object.")
            return

        title = str(embed.get("title", ""))
        description = str(embed.get("description", ""))
        if len(title) > 256:
            errors.append(f"Embed {index} title exceeds 256 characters.")
        if len(description) > 4096:
            errors.append(f"Embed {index} description exceeds 4096 characters.")

        color = embed.get("color")
        if isinstance(color, str) and color and not HEX_COLOR_RE.fullmatch(color):
            errors.append(f"Embed {index} color must be valid HEX.")
        elif isinstance(color, int) and not 0 <= color <= 0xFFFFFF:
            errors.append(f"Embed {index} color is outside Discord's range.")

        fields = embed.get("fields", [])
        if fields and not isinstance(fields, list):
            errors.append(f"Embed {index} fields must be a list.")
            return
        if len(fields) > 25:
            errors.append(f"Embed {index} has more than 25 fields.")
        for field_index, field in enumerate(fields, start=1):
            if not isinstance(field, dict):
                errors.append(f"Embed {index} field {field_index} must be an object.")
                continue
            if len(str(field.get("name", ""))) > 256:
                errors.append(f"Embed {index} field {field_index} name exceeds 256.")
            if len(str(field.get("value", ""))) > 1024:
                errors.append(f"Embed {index} field {field_index} value exceeds 1024.")
