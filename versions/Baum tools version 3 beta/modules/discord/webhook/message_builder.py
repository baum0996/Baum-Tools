from __future__ import annotations

import logging
from copy import deepcopy

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from modules.discord.webhook.preview import WebhookPreview
from modules.discord.webhook.utils import (
    JsonDict,
    default_payload,
    hex_to_discord_int,
    now_iso_timestamp,
)
from settings import SettingsStore
from ui_theme import (
    CRT_DANGER,
    CRT_GREEN,
    CRT_MUTED,
    CRT_PROMPT,
    CRT_WARNING,
    crt_data_table,
    crt_footer,
    crt_header,
    crt_menu,
    crt_message,
    crt_panel,
)
from utils import clear_console, terminal_width


class MessageBuilder:
    def __init__(
        self,
        console: Console,
        settings_store: SettingsStore,
        payload: JsonDict | None = None,
    ) -> None:
        self.console = console
        self.settings_store = settings_store
        self.payload = deepcopy(payload) if payload else default_payload()
        self.preview = WebhookPreview()
        self._logger = logging.getLogger(__name__)

    def open(self) -> JsonDict:
        while True:
            self._render()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2", "3", "4", "5", "6"],
                show_choices=False,
            )
            if choice == "1":
                self._edit_general()
            elif choice == "2":
                self._embed_menu()
            elif choice == "3":
                self._render_preview(wait=True)
            elif choice == "4":
                self.payload = default_payload()
            elif choice == "5":
                self._apply_current_timestamp()
            elif choice == "6":
                return self.payload

    def _render(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            crt_panel(
                self.preview.render(self.payload),
                title="Message Builder",
                border_style=CRT_GREEN,
                width=min(terminal_width(), 120),
            )
        )
        self.console.print()

        self.console.print(
            crt_menu(
                "Editor",
                (
                    ("1", "General Message Settings"),
                    ("2", "Embeds"),
                    ("3", "Live Preview"),
                    ("4", "Reset Payload"),
                    ("5", "Set Current Timestamp on Selected Embed"),
                    ("6", "Back"),
                ),
            )
        )
        self.console.print(crt_footer("Webhook Builder", "PRESS 6 TO GO BACK"))
        self.console.print()

    def _edit_general(self) -> None:
        while True:
            self._clear_if_enabled()
            table = crt_data_table("General Message Settings")
            table.add_column("Key", style=f"bold {CRT_GREEN}")
            table.add_column("Setting", style=CRT_GREEN)
            table.add_column("Value", overflow="fold", style=CRT_MUTED)
            table.add_row("01", "Webhook URL", self.payload.get("webhook_url") or "-")
            table.add_row("02", "Username Override", self.payload.get("username") or "-")
            table.add_row("03", "Avatar URL", self.payload.get("avatar_url") or "-")
            table.add_row("04", "Content", self.payload.get("content") or "-")
            table.add_row("05", "TTS", "Enabled" if self.payload.get("tts") else "Disabled")
            table.add_row(
                "06",
                "Allowed Mentions",
                str(self.payload.get("allowed_mentions") or {}),
            )
            table.add_row(
                "07",
                "Suppress Embeds",
                "Enabled" if self.payload.get("suppress_embeds") else "Disabled",
            )
            table.add_row("08", "Back", "Return to builder")
            self.console.print()
            self.console.print(crt_header("General Settings"))
            self.console.print(table)
            self.console.print(crt_footer("Webhook Builder", "PRESS 8 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT SETTING",
                choices=[str(index) for index in range(1, 9)],
                show_choices=False,
            )
            if choice == "1":
                self.payload["webhook_url"] = Prompt.ask("Webhook URL", default="")
            elif choice == "2":
                self.payload["username"] = Prompt.ask("Username Override", default="")
            elif choice == "3":
                self.payload["avatar_url"] = Prompt.ask("Avatar URL", default="")
            elif choice == "4":
                self.payload["content"] = Prompt.ask("Content", default="")
            elif choice == "5":
                self.payload["tts"] = not bool(self.payload.get("tts"))
            elif choice == "6":
                self._edit_allowed_mentions()
            elif choice == "7":
                self.payload["suppress_embeds"] = not bool(
                    self.payload.get("suppress_embeds")
                )
            elif choice == "8":
                return

    def _edit_allowed_mentions(self) -> None:
        current = self.payload.get("allowed_mentions")
        if not isinstance(current, dict):
            current = {}
        parse: list[str] = []
        if Confirm.ask("Allow @everyone/@here?", default=False):
            parse.append("everyone")
        if Confirm.ask("Allow role mentions?", default=False):
            parse.append("roles")
        if Confirm.ask("Allow user mentions?", default=False):
            parse.append("users")
        role_ids = self._split_ids(
            Prompt.ask(
                "Explicit allowed role IDs",
                default=", ".join(current.get("roles", []))
                if isinstance(current.get("roles"), list)
                else "",
            )
        )
        user_ids = self._split_ids(
            Prompt.ask(
                "Explicit allowed user IDs",
                default=", ".join(current.get("users", []))
                if isinstance(current.get("users"), list)
                else "",
            )
        )
        self.payload["allowed_mentions"] = {
            "parse": parse,
            "roles": role_ids,
            "users": user_ids,
            "replied_user": Confirm.ask("Mention replied user?", default=False),
        }

    def _embed_menu(self) -> None:
        while True:
            self._clear_if_enabled()
            embeds = self._embeds()
            table = crt_data_table("Embeds")
            table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
            table.add_column("Name", style=CRT_GREEN)
            table.add_column("Title", overflow="fold", style=CRT_MUTED)
            table.add_column("Fields", justify="right", style=CRT_MUTED)
            if embeds:
                for index, embed in enumerate(embeds, start=1):
                    table.add_row(
                        str(index),
                        str(embed.get("_label") or f"Embed {index}"),
                        str(embed.get("title") or "-"),
                        str(len(embed.get("fields", []))),
                    )
            else:
                table.add_row("-", "No embeds", "-", "-")
            self.console.print()
            self.console.print(crt_header("Embeds"))
            self.console.print(table)

            self.console.print(
                crt_menu(
                    "Embed Actions",
                    (
                        ("1", "Create Embed"),
                        ("2", "Edit Embed"),
                        ("3", "Delete Embed"),
                        ("4", "Duplicate Embed"),
                        ("5", "Rename Embed"),
                        ("6", "Move Up"),
                        ("7", "Move Down"),
                        ("8", "Back"),
                    ),
                )
            )
            self.console.print(crt_footer("Webhook Builder", "PRESS 8 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=[str(index) for index in range(1, 9)],
                show_choices=False,
            )
            if choice == "1":
                self._create_embed()
            elif choice == "2":
                embed = self._select_embed()
                if embed is not None:
                    self._edit_embed(embed)
            elif choice == "3":
                index = self._select_embed_index()
                if index is not None and Confirm.ask("Delete embed?", default=False):
                    embeds.pop(index)
            elif choice == "4":
                index = self._select_embed_index()
                if index is not None:
                    embeds.insert(index + 1, deepcopy(embeds[index]))
            elif choice == "5":
                embed = self._select_embed()
                if embed is not None:
                    embed["_label"] = Prompt.ask(
                        "Embed name",
                        default=str(embed.get("_label") or "Embed"),
                    )
            elif choice == "6":
                index = self._select_embed_index()
                if index is not None and index > 0:
                    embeds[index - 1], embeds[index] = embeds[index], embeds[index - 1]
            elif choice == "7":
                index = self._select_embed_index()
                if index is not None and index < len(embeds) - 1:
                    embeds[index + 1], embeds[index] = embeds[index], embeds[index + 1]
            elif choice == "8":
                return

    def _create_embed(self) -> None:
        embed: JsonDict = {
            "_label": f"Embed {len(self._embeds()) + 1}",
            "title": "",
            "description": "",
            "fields": [],
        }
        self._embeds().append(embed)
        self._edit_embed(embed)

    def _edit_embed(self, embed: JsonDict) -> None:
        while True:
            self._clear_if_enabled()
            self.console.print(self.preview._embed_panel(1, embed))
            self.console.print(
                crt_menu(
                    "Edit Embed",
                    (
                        ("1", "General"),
                        ("2", "Author"),
                        ("3", "Footer"),
                        ("4", "Images"),
                        ("5", "Fields"),
                        ("6", "Back"),
                    ),
                )
            )
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2", "3", "4", "5", "6"],
                show_choices=False,
            )
            if choice == "1":
                self._edit_embed_general(embed)
            elif choice == "2":
                self._edit_nested(embed, "author", ("name", "url", "icon_url"))
            elif choice == "3":
                self._edit_nested(embed, "footer", ("text", "icon_url"))
            elif choice == "4":
                self._edit_images(embed)
            elif choice == "5":
                self._fields_menu(embed)
            elif choice == "6":
                return

    def _edit_embed_general(self, embed: JsonDict) -> None:
        embed["title"] = Prompt.ask("Title", default=str(embed.get("title") or ""))
        embed["description"] = Prompt.ask(
            "Description",
            default=str(embed.get("description") or ""),
        )
        embed["url"] = Prompt.ask("URL", default=str(embed.get("url") or ""))
        color = Prompt.ask("HEX Color", default="")
        if color:
            try:
                embed["color"] = hex_to_discord_int(color)
            except ValueError as exc:
                self._message("Invalid HEX Color", str(exc), CRT_DANGER)
        timestamp = Prompt.ask(
            "Timestamp ISO-8601",
            default=str(embed.get("timestamp") or ""),
        )
        if timestamp:
            embed["timestamp"] = timestamp

    def _edit_nested(self, embed: JsonDict, key: str, fields: tuple[str, ...]) -> None:
        current = embed.get(key)
        if not isinstance(current, dict):
            current = {}
        for field in fields:
            current[field] = Prompt.ask(
                field.replace("_", " ").title(),
                default=str(current.get(field) or ""),
            )
        embed[key] = current

    def _edit_images(self, embed: JsonDict) -> None:
        thumbnail = Prompt.ask(
            "Thumbnail URL",
            default=str(
                (embed.get("thumbnail") or {}).get("url")
                if isinstance(embed.get("thumbnail"), dict)
                else ""
            ),
        )
        image = Prompt.ask(
            "Image URL",
            default=str(
                (embed.get("image") or {}).get("url")
                if isinstance(embed.get("image"), dict)
                else ""
            ),
        )
        embed["thumbnail"] = {"url": thumbnail}
        embed["image"] = {"url": image}

    def _fields_menu(self, embed: JsonDict) -> None:
        fields = embed.setdefault("fields", [])
        if not isinstance(fields, list):
            fields = []
            embed["fields"] = fields

        while True:
            self._clear_if_enabled()
            table = crt_data_table("Fields")
            table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
            table.add_column("Name", overflow="fold", style=CRT_GREEN)
            table.add_column("Value", overflow="fold", style=CRT_MUTED)
            table.add_column("Inline", justify="center", style=CRT_MUTED)
            if fields:
                for index, field in enumerate(fields, start=1):
                    table.add_row(
                        str(index),
                        str(field.get("name") or "-"),
                        str(field.get("value") or "-"),
                        "Yes" if field.get("inline") else "No",
                    )
            else:
                table.add_row("-", "No fields", "-", "-")
            self.console.print()
            self.console.print(crt_header("Fields"))
            self.console.print(table)
            self.console.print(crt_footer("Webhook Builder", "PRESS 7 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} [1] CREATE  [2] EDIT  [3] DELETE  [4] DUPLICATE  "
                "[5] MOVE UP  [6] MOVE DOWN  [7] BACK",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                show_choices=False,
            )
            if choice == "1":
                fields.append(self._prompt_field())
            elif choice == "2":
                index = self._select_field_index(fields)
                if index is not None:
                    fields[index] = self._prompt_field(fields[index])
            elif choice == "3":
                index = self._select_field_index(fields)
                if index is not None and Confirm.ask("Delete field?", default=False):
                    fields.pop(index)
            elif choice == "4":
                index = self._select_field_index(fields)
                if index is not None:
                    fields.insert(index + 1, deepcopy(fields[index]))
            elif choice == "5":
                index = self._select_field_index(fields)
                if index is not None and index > 0:
                    fields[index - 1], fields[index] = fields[index], fields[index - 1]
            elif choice == "6":
                index = self._select_field_index(fields)
                if index is not None and index < len(fields) - 1:
                    fields[index + 1], fields[index] = fields[index], fields[index + 1]
            elif choice == "7":
                return

    def _prompt_field(self, field: JsonDict | None = None) -> JsonDict:
        current = field or {}
        return {
            "name": Prompt.ask("Field Name", default=str(current.get("name") or "")),
            "value": Prompt.ask("Field Value", default=str(current.get("value") or "")),
            "inline": Confirm.ask("Inline?", default=bool(current.get("inline"))),
        }

    def _select_embed(self) -> JsonDict | None:
        index = self._select_embed_index()
        if index is None:
            return None
        return self._embeds()[index]

    def _select_embed_index(self) -> int | None:
        embeds = self._embeds()
        if not embeds:
            self._message("Embeds", "No embeds available.", CRT_WARNING)
            return None
        index = IntPrompt.ask("Embed number", default=1) - 1
        if index < 0 or index >= len(embeds):
            self._message("Embeds", "Embed number is out of range.", CRT_DANGER)
            return None
        return index

    def _select_field_index(self, fields: list[JsonDict]) -> int | None:
        if not fields:
            self._message("Fields", "No fields available.", CRT_WARNING)
            return None
        index = IntPrompt.ask("Field number", default=1) - 1
        if index < 0 or index >= len(fields):
            self._message("Fields", "Field number is out of range.", CRT_DANGER)
            return None
        return index

    def _apply_current_timestamp(self) -> None:
        embed = self._select_embed()
        if embed is not None:
            embed["timestamp"] = now_iso_timestamp()

    def _render_preview(self, wait: bool = False) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(self.preview.render(self.payload))
        self.console.print()
        if wait:
            Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO RETURN", default="")

    def _embeds(self) -> list[JsonDict]:
        embeds = self.payload.setdefault("embeds", [])
        if not isinstance(embeds, list):
            embeds = []
            self.payload["embeds"] = embeds
        return embeds

    def _message(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_message(title, message, style))
        self.console.print()
        Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO RETURN", default="")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

    @staticmethod
    def _split_ids(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]
