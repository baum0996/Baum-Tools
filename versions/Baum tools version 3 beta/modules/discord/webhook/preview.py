from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from modules.discord.webhook.utils import JsonDict, discord_int_to_hex
from ui_theme import CRT_DIM, CRT_GREEN, CRT_MUTED, crt_panel


class WebhookPreview:
    def render(self, payload: JsonDict) -> Group:
        parts: list[Any] = [self._message_table(payload)]
        embeds = payload.get("embeds", [])
        if isinstance(embeds, list) and embeds:
            for index, embed in enumerate(embeds, start=1):
                if isinstance(embed, dict):
                    parts.append(self._embed_panel(index, embed))
        else:
            parts.append(crt_panel("No embeds created.", "Embeds", border_style=CRT_DIM))
        parts.append(self._counts_panel(payload))
        return Group(*parts)

    def _message_table(self, payload: JsonDict) -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(style=f"bold {CRT_GREEN}", no_wrap=True)
        table.add_column(style=CRT_MUTED, overflow="fold")
        table.add_row("Username", str(payload.get("username") or "Default webhook name"))
        table.add_row("Avatar URL", str(payload.get("avatar_url") or "-"))
        table.add_row("Webhook URL", self._redact_url(str(payload.get("webhook_url") or "")))
        table.add_row("TTS", "Enabled" if payload.get("tts") else "Disabled")
        table.add_row(
            "Suppress Embeds",
            "Enabled" if payload.get("suppress_embeds") else "Disabled",
        )
        table.add_row("Allowed Mentions", str(payload.get("allowed_mentions") or {}))
        table.add_row("Content", str(payload.get("content") or "-"))
        return crt_panel(table, "Message")

    def _embed_panel(self, index: int, embed: JsonDict) -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(style=f"bold {CRT_GREEN}", no_wrap=True)
        table.add_column(style=CRT_MUTED, overflow="fold")
        label = str(embed.get("_label") or f"Embed {index}")
        color = self._color_text(embed.get("color"))

        table.add_row("Title", str(embed.get("title") or "-"))
        table.add_row("Description", str(embed.get("description") or "-"))
        table.add_row("URL", str(embed.get("url") or "-"))
        table.add_row("Color", color)
        table.add_row("Timestamp", str(embed.get("timestamp") or "-"))
        table.add_row("Author", self._nested(embed.get("author"), ("name", "url", "icon_url")))
        table.add_row("Footer", self._nested(embed.get("footer"), ("text", "icon_url")))
        table.add_row("Thumbnail", self._nested(embed.get("thumbnail"), ("url",)))
        table.add_row("Image", self._nested(embed.get("image"), ("url",)))

        fields = embed.get("fields", [])
        if isinstance(fields, list) and fields:
            field_table = Table(box=box.SQUARE, border_style=CRT_DIM)
            field_table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
            field_table.add_column("Name", overflow="fold", style=CRT_GREEN)
            field_table.add_column("Value", overflow="fold", style=CRT_MUTED)
            field_table.add_column("Inline", justify="center", style=CRT_MUTED)
            for field_index, field in enumerate(fields, start=1):
                if not isinstance(field, dict):
                    continue
                field_table.add_row(
                    str(field_index),
                    str(field.get("name") or "-"),
                    str(field.get("value") or "-"),
                    "Yes" if field.get("inline") else "No",
                )
            content = Group(table, field_table)
        else:
            content = table

        border = discord_int_to_hex(embed.get("color")) or CRT_GREEN
        return Panel(content, title=f"[ {label.upper()} ]", border_style=border, box=box.SQUARE)

    def _counts_panel(self, payload: JsonDict) -> Panel:
        content_length = len(str(payload.get("content") or ""))
        embed_count = len(payload.get("embeds", []))
        field_count = 0
        embed_chars = 0
        for embed in payload.get("embeds", []):
            if not isinstance(embed, dict):
                continue
            embed_chars += len(str(embed.get("title") or ""))
            embed_chars += len(str(embed.get("description") or ""))
            fields = embed.get("fields", [])
            if isinstance(fields, list):
                field_count += len(fields)
                for field in fields:
                    if isinstance(field, dict):
                        embed_chars += len(str(field.get("name") or ""))
                        embed_chars += len(str(field.get("value") or ""))

        table = Table.grid(padding=(0, 2))
        table.add_column(style=f"bold {CRT_GREEN}")
        table.add_column(style=CRT_MUTED, justify="right")
        table.add_row("Content", f"{content_length}/2000")
        table.add_row("Embeds", f"{embed_count}/10")
        table.add_row("Fields", str(field_count))
        table.add_row("Embed Characters", f"{embed_chars}/6000")
        return crt_panel(table, "Character Counts")

    @staticmethod
    def _nested(value: object, keys: tuple[str, ...]) -> str:
        if not isinstance(value, dict):
            return "-"
        parts = [f"{key}: {value.get(key)}" for key in keys if value.get(key)]
        return " | ".join(parts) if parts else "-"

    @staticmethod
    def _color_text(value: object) -> Text:
        color = discord_int_to_hex(value)
        if not color:
            return Text("-")
        text = Text(f"{color}  ")
        text.append("      ", style=f"on {color}")
        return text

    @staticmethod
    def _redact_url(value: str) -> str:
        if not value:
            return "-"
        return value[:55] + "..." if len(value) > 58 else value
