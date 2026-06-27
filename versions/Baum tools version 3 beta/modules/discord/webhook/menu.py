from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt

from modules.discord.webhook.json_io import WebhookJsonIO
from modules.discord.webhook.message_builder import MessageBuilder
from modules.discord.webhook.preview import WebhookPreview
from modules.discord.webhook.settings import WebhookSettingsStore
from modules.discord.webhook.templates import TemplateStore
from modules.discord.webhook.utils import (
    EXPORT_DIR,
    JsonDict,
    clean_payload_for_send,
    default_payload,
    discord_api_headers,
    ensure_webhook_directories,
    unique_path,
)
from modules.discord.webhook.validation import ValidationResult, WebhookValidator
from modules.discord.webhook.webhook_info import WebhookInfoClient
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


class WebhookMenu:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store
        self.payload = default_payload()
        self.validator = WebhookValidator()
        self.json_io = WebhookJsonIO(self.validator)
        self.templates = TemplateStore(self.validator)
        self.preview = WebhookPreview()
        self.webhook_settings = WebhookSettingsStore()
        self.info_client = WebhookInfoClient(self.validator)
        self._logger = logging.getLogger(__name__)
        ensure_webhook_directories()

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=[str(index) for index in range(1, 10)],
                show_choices=False,
            )
            if choice == "1":
                self.payload = MessageBuilder(
                    self.console,
                    self.settings_store,
                    self.payload,
                ).open()
            elif choice == "2":
                self._templates_menu()
            elif choice == "3":
                self._json_import()
            elif choice == "4":
                self._json_export()
            elif choice == "5":
                self._webhook_information()
            elif choice == "6":
                self._validate_webhook()
            elif choice == "7":
                self._test_webhook()
            elif choice == "8":
                self._settings_menu()
            elif choice == "9":
                return

    def _render(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Webhook"))
        self.console.print()

        summary = self.validator.validate_payload(self.payload)
        self.console.print(
            crt_menu(
                "Webhook",
                (
                    ("1", "Message Builder"),
                    ("2", "Templates"),
                    ("3", "JSON Import"),
                    ("4", "JSON Export"),
                    ("5", "Webhook Information"),
                    ("6", "Validate Webhook"),
                    ("7", "Test Webhook"),
                    ("8", "Settings"),
                    ("9", "Back"),
                ),
            )
        )
        self.console.print(
            crt_panel(
                self._payload_summary(summary),
                title="Current Payload",
                border_style=CRT_GREEN if summary.status == "Valid" else CRT_WARNING,
                width=min(terminal_width(), 110),
            )
        )
        self.console.print(crt_footer("Webhook", "PRESS 9 TO GO BACK"))
        self.console.print()

    def _templates_menu(self) -> None:
        query = ""
        while True:
            self._clear_if_enabled()
            templates = self.templates.list_templates(query)
            table = crt_data_table("Templates")
            table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
            table.add_column("Name", overflow="fold", style=CRT_GREEN)
            table.add_column("Path", overflow="fold", style=CRT_MUTED)
            if templates:
                for index, path in enumerate(templates, start=1):
                    table.add_row(str(index), path.stem, str(path))
            else:
                table.add_row("-", "No templates found", "-")
            self.console.print()
            self.console.print(crt_header("Templates"))
            self.console.print(table)
            self.console.print(crt_footer("Webhook", "PRESS 7 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} [1] SAVE  [2] LOAD  [3] RENAME  [4] DUPLICATE  "
                "[5] DELETE  [6] SEARCH  [7] BACK",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                show_choices=False,
            )
            if choice == "1":
                name = Prompt.ask("Template name", default="webhook_payload")
                path = self.templates.save(name, self.payload)
                self._message("Template Saved", str(path), CRT_GREEN)
            elif choice == "2":
                path = self._select_path(templates, "Template number")
                if path:
                    payload, result = self.templates.load(path)
                    if payload is not None:
                        self.payload = payload
                    self._show_validation("Template Load", result)
            elif choice == "3":
                path = self._select_path(templates, "Template number")
                if path:
                    new_name = Prompt.ask("New template name", default=path.stem)
                    target = self.templates.rename(path, new_name)
                    self._message("Template Renamed", str(target), CRT_GREEN)
            elif choice == "4":
                path = self._select_path(templates, "Template number")
                if path:
                    target = self.templates.duplicate(path)
                    self._message("Template Duplicated", str(target), CRT_GREEN)
            elif choice == "5":
                path = self._select_path(templates, "Template number")
                if path and Confirm.ask("Delete template?", default=False):
                    self.templates.delete(path)
            elif choice == "6":
                query = Prompt.ask("Search", default="")
            elif choice == "7":
                return

    def _json_import(self) -> None:
        path = Path(Prompt.ask("JSON file path")).expanduser()
        payload, result = self.json_io.import_from_file(path)
        if payload is not None:
            self.payload = payload
        self._show_validation("JSON Import", result)

    def _json_export(self) -> None:
        default_path = unique_path(EXPORT_DIR, "webhook_payload", ".json")
        path = Path(Prompt.ask("Export path", default=str(default_path))).expanduser()
        try:
            self.json_io.export_to_file(path, self.payload)
        except OSError as exc:
            self._logger.exception("Failed to export webhook JSON.")
            self._message("JSON Export Failed", str(exc), CRT_DANGER)
            return

        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            crt_panel(
                self.json_io.to_pretty_json(self.payload),
                title=f"Exported: {path}",
                border_style=CRT_GREEN,
                width=min(terminal_width(), 120),
            )
        )
        self.console.print()
        self._wait_for_back()

    def _webhook_information(self) -> None:
        webhook_url = self._prompt_webhook_url()
        if not webhook_url:
            return

        with self._progress("Fetching webhook information..."):
            info = self.info_client.fetch(
                webhook_url,
                self.webhook_settings.settings.request_timeout_seconds,
            )

        table = crt_data_table("Webhook Information")
        table.add_column("Property", style=f"bold {CRT_GREEN}")
        table.add_column("Value", overflow="fold", style=CRT_MUTED)
        table.add_row("Validation Status", info.status)
        table.add_row("Webhook Name", info.webhook_name or "-")
        table.add_row("Webhook ID", info.webhook_id or "-")
        table.add_row("Guild ID", info.guild_id or "-")
        table.add_row("Channel ID", info.channel_id or "-")
        table.add_row("Avatar", info.avatar or "-")
        table.add_row("HTTP Status", str(info.http_status or "-"))
        if info.error:
            table.add_row("Error", info.error)

        self._clear_if_enabled()
        self.console.print()
        self.console.print(table)
        self.console.print()
        self._wait_for_back()

    def _validate_webhook(self) -> None:
        webhook_url = self._prompt_webhook_url()
        if not webhook_url:
            return

        format_valid = self.validator.validate_webhook_format(webhook_url)
        if not format_valid:
            self._show_validation(
                "Validate Webhook",
                ValidationResult("Invalid", ["Webhook URL format is invalid."], []),
            )
            return

        with self._progress("Checking Discord webhook..."):
            result = self.validator.validate_webhook_url(
                webhook_url,
                self.webhook_settings.settings.request_timeout_seconds,
            )
        self._show_validation("Validate Webhook", result)

    def _test_webhook(self) -> None:
        test_payload = {
            "webhook_url": self._prompt_webhook_url(),
            "username": Prompt.ask(
                "Username",
                default=self.payload.get("username")
                or self.webhook_settings.settings.default_username,
            ),
            "avatar_url": Prompt.ask(
                "Avatar URL",
                default=self.payload.get("avatar_url")
                or self.webhook_settings.settings.default_avatar_url,
            ),
            "content": Prompt.ask(
                "Content",
                default=self.webhook_settings.settings.default_test_content,
            ),
            "tts": False,
            "allowed_mentions": {"parse": []},
            "suppress_embeds": False,
            "embeds": [],
        }
        if not test_payload["webhook_url"]:
            return
        if Confirm.ask("Add optional embed?", default=False):
            test_payload["embeds"].append(
                {
                    "title": Prompt.ask("Embed title", default="BAUM TOOLS Test"),
                    "description": Prompt.ask("Embed description", default="Webhook test message."),
                    "color": 0x5865F2,
                }
            )

        result = self.validator.validate_payload(test_payload)
        if result.errors:
            self._show_validation("Test Webhook", result)
            return

        with self._progress("Sending test webhook..."):
            status, body = self._send_webhook(test_payload)
        self._message(
            "Test Webhook",
            f"HTTP Status: {status}\n\n{body or '-'}",
            CRT_GREEN if 200 <= status < 300 else CRT_DANGER,
        )

    def _settings_menu(self) -> None:
        store = self.webhook_settings
        while True:
            self._clear_if_enabled()
            settings = store.settings
            table = crt_data_table("Webhook Settings")
            table.add_column("Key", style=f"bold {CRT_GREEN}")
            table.add_column("Setting", style=CRT_GREEN)
            table.add_column("Value", overflow="fold", style=CRT_MUTED)
            table.add_row("1", "Default Username", settings.default_username or "-")
            table.add_row("2", "Default Avatar URL", settings.default_avatar_url or "-")
            table.add_row("3", "Default Test Content", settings.default_test_content)
            table.add_row(
                "4",
                "Request Timeout Seconds",
                str(settings.request_timeout_seconds),
            )
            table.add_row("5", "Preview Width", str(settings.preview_width))
            table.add_row("6", "Back", "Return to webhook menu")
            self.console.print()
            self.console.print(crt_header("Webhook Settings"))
            self.console.print(table)
            self.console.print(crt_footer("Webhook", "PRESS 6 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT SETTING",
                choices=["1", "2", "3", "4", "5", "6"],
                show_choices=False,
            )
            if choice == "1":
                settings.default_username = Prompt.ask("Default Username", default="")
            elif choice == "2":
                settings.default_avatar_url = Prompt.ask("Default Avatar URL", default="")
            elif choice == "3":
                settings.default_test_content = Prompt.ask(
                    "Default Test Content",
                    default=settings.default_test_content,
                )
            elif choice == "4":
                settings.request_timeout_seconds = float(
                    Prompt.ask("Request Timeout Seconds", default="8")
                )
            elif choice == "5":
                settings.preview_width = int(Prompt.ask("Preview Width", default="110"))
            elif choice == "6":
                store.save()
                return
            store.save()

    def _send_webhook(self, payload: JsonDict) -> tuple[int, str]:
        webhook_url = str(payload["webhook_url"])
        body = json.dumps(clean_payload_for_send(payload)).encode("utf-8")
        request = Request(
            webhook_url,
            data=body,
            headers=discord_api_headers("application/json"),
            method="POST",
        )
        try:
            with urlopen(
                request,
                timeout=self.webhook_settings.settings.request_timeout_seconds,
            ) as response:
                response_body = response.read(4096).decode("utf-8", errors="replace")
                return response.status, response_body
        except HTTPError as exc:
            response_body = exc.read(4096).decode("utf-8", errors="replace")
            return exc.code, response_body
        except (TimeoutError, URLError, OSError) as exc:
            self._logger.exception("Failed to send webhook.")
            return 0, str(exc)

    def _show_validation(self, title: str, result: ValidationResult) -> None:
        self._clear_if_enabled()
        table = crt_data_table(title)
        table.add_column("Type", style=f"bold {CRT_GREEN}")
        table.add_column("Message", overflow="fold", style=CRT_MUTED)
        table.add_row("Status", result.status)
        if result.http_status is not None:
            table.add_row("HTTP Response", str(result.http_status))
        for error in result.errors:
            table.add_row("Error", error)
        for warning in result.warnings:
            table.add_row("Warning", warning)
        if result.response_text:
            table.add_row("Response", result.response_text)
        self.console.print()
        self.console.print(table)
        self.console.print()
        self._wait_for_back()

    def _payload_summary(self, result: ValidationResult) -> str:
        embeds = self.payload.get("embeds", [])
        embed_count = len(embeds) if isinstance(embeds, list) else 0
        content_count = len(str(self.payload.get("content") or ""))
        messages = [f"Status: {result.status}", f"Content: {content_count}/2000"]
        messages.append(f"Embeds: {embed_count}/10")
        if result.errors:
            messages.append(f"Errors: {len(result.errors)}")
        if result.warnings:
            messages.append(f"Warnings: {len(result.warnings)}")
        return " | ".join(messages)

    def _select_path(self, paths: list[Path], prompt: str) -> Path | None:
        if not paths:
            self._message("Templates", "No templates available.", CRT_WARNING)
            return None
        index = IntPrompt.ask(prompt, default=1) - 1
        if index < 0 or index >= len(paths):
            self._message("Templates", "Selection is out of range.", CRT_DANGER)
            return None
        return paths[index]

    def _prompt_webhook_url(self) -> str:
        current = str(self.payload.get("webhook_url") or "")
        return Prompt.ask("Webhook URL", default=current)

    def _message(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_message(title, message, style))
        self.console.print()
        self._wait_for_back()

    @contextmanager
    def _progress(self, message: str) -> Iterator[None]:
        progress = Progress(
            SpinnerColumn(style=CRT_GREEN),
            TextColumn(f"[{CRT_GREEN}]{{task.description}}[/{CRT_GREEN}]"),
            transient=True,
            console=self.console,
        )
        with progress:
            progress.add_task(message, total=None)
            yield

    def _wait_for_back(self) -> None:
        Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO RETURN", default="")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()
