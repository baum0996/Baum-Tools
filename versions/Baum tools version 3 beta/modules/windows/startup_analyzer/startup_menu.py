from __future__ import annotations

import logging

from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from modules.windows.startup_analyzer.startup_analyzer import (
    StartupAnalysis,
    StartupAnalyzer,
    StartupEntry,
)
from settings import SettingsStore
from ui_theme import (
    CRT_DANGER,
    CRT_GREEN,
    CRT_MUTED,
    CRT_PROMPT,
    crt_footer,
    crt_header,
    crt_menu,
    crt_message,
)
from utils import clear_console


class StartupAnalyzerPage:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store
        self.analyzer = StartupAnalyzer()
        self._logger = logging.getLogger(__name__)

    def open(self) -> None:
        while True:
            self._render_header()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2"],
                show_choices=False,
            )
            if choice == "1":
                self._run_scan()
            elif choice == "2":
                return

    def _render_header(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Startup Analyzer"))
        self.console.print(
            crt_message("Info", "Read-only inspection of Windows startup entries.")
        )
        self.console.print()
        self.console.print(
            crt_menu("Actions", (("1", "Scan Startup Entries"), ("2", "Back")))
        )
        self.console.print(crt_footer("Windows", "PRESS 2 TO GO BACK"))
        self.console.print()

    def _run_scan(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            crt_message(
                "Startup Analyzer",
                "Scanning startup entry locations in read-only mode...",
            )
        )

        try:
            analysis = self.analyzer.scan()
        except RuntimeError as exc:
            self._logger.exception("Startup Analyzer is unavailable.")
            self._message("Startup Analyzer", str(exc), CRT_DANGER)
            return
        except Exception as exc:
            self._logger.exception("Startup Analyzer failed.")
            self._message("Startup Analyzer Failed", str(exc), CRT_DANGER)
            return

        self._render_results(analysis)

    def _render_results(self, analysis: StartupAnalysis) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Startup Analyzer"))
        self.console.print()

        self._render_entries_table(
            "Registry Startup Entries",
            analysis.registry_entries,
            CRT_GREEN,
        )
        self._render_entries_table(
            "Startup Folder Entries",
            analysis.folder_entries,
            CRT_GREEN,
        )
        self._render_entries_table(
            "Scheduled Tasks (Startup-related)",
            analysis.scheduled_tasks,
            CRT_GREEN,
        )
        self._render_summary(analysis)
        self.console.print(crt_footer("Windows", "PRESS ENTER TO GO BACK"))
        self._wait_for_back()

    def _render_entries_table(
        self,
        title: str,
        entries: list[StartupEntry],
        border_style: str,
    ) -> None:
        table = Table(title=title.upper(), box=box.SQUARE, border_style=border_style)
        table.add_column("Entry Name", style=f"bold {CRT_GREEN}", overflow="fold")
        table.add_column("File Path", style=CRT_MUTED, overflow="fold")
        table.add_column("Source", style=CRT_GREEN, overflow="fold")
        table.add_column("Publisher", style=CRT_MUTED, overflow="fold")
        table.add_column("Indicator", style=CRT_DANGER, overflow="fold")

        if entries:
            for entry in entries:
                table.add_row(
                    entry.name,
                    entry.file_path,
                    entry.source,
                    entry.publisher or "-",
                    entry.indicator or "-",
                )
        else:
            table.add_row("No entries found", "-", "-", "-", "-")

        self.console.print(table)
        self.console.print()

    def _render_summary(self, analysis: StartupAnalysis) -> None:
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style=f"bold {CRT_GREEN}")
        summary.add_column(justify="right", style=CRT_MUTED)
        summary.add_row("Total startup entries", str(analysis.total_entries))
        summary.add_row("Registry entries", str(len(analysis.registry_entries)))
        summary.add_row("Folder entries", str(len(analysis.folder_entries)))
        summary.add_row("Scheduled tasks", str(len(analysis.scheduled_tasks)))

        self.console.print(
            crt_message(
                "Summary",
                summary,
                CRT_GREEN,
            )
        )
        self.console.print()

    def _message(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_message(title, message, style))
        self.console.print()
        self._wait_for_back()

    def _wait_for_back(self) -> None:
        Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO RETURN", default="")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()
