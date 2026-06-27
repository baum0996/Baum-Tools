from __future__ import annotations

import logging

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from modules.windows.startup_analyzer.startup_analyzer import (
    StartupAnalysis,
    StartupAnalyzer,
    StartupEntry,
)
from settings import SettingsStore
from utils import clear_console, terminal_width


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
                "[bold cyan]Select[/bold cyan]",
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
        self.console.print(
            Panel(
                "Read-only inspection of Windows startup entries.",
                title="Startup Analyzer",
                border_style="cyan",
                width=min(terminal_width(), 110),
            )
        )
        self.console.print()

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right", style="bold cyan")
        table.add_column(style="white")
        table.add_row("[1]", "Scan Startup Entries")
        table.add_row("[2]", "Back")

        self.console.print(Panel(table, title="Actions", border_style="blue"))
        self.console.print()

    def _run_scan(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            Panel(
                "Scanning startup entry locations in read-only mode...",
                title="Startup Analyzer",
                border_style="cyan",
            )
        )

        try:
            analysis = self.analyzer.scan()
        except RuntimeError as exc:
            self._logger.exception("Startup Analyzer is unavailable.")
            self._message("Startup Analyzer", str(exc), "red")
            return
        except Exception as exc:
            self._logger.exception("Startup Analyzer failed.")
            self._message("Startup Analyzer Failed", str(exc), "red")
            return

        self._render_results(analysis)

    def _render_results(self, analysis: StartupAnalysis) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(Panel.fit("Startup Analyzer", border_style="cyan"))
        self.console.print()

        self._render_entries_table(
            "Registry Startup Entries",
            analysis.registry_entries,
            "blue",
        )
        self._render_entries_table(
            "Startup Folder Entries",
            analysis.folder_entries,
            "blue",
        )
        self._render_entries_table(
            "Scheduled Tasks (Startup-related)",
            analysis.scheduled_tasks,
            "blue",
        )
        self._render_summary(analysis)
        self._wait_for_back()

    def _render_entries_table(
        self,
        title: str,
        entries: list[StartupEntry],
        border_style: str,
    ) -> None:
        table = Table(title=title, box=box.SIMPLE_HEAVY, border_style=border_style)
        table.add_column("Entry Name", style="bold cyan", overflow="fold")
        table.add_column("File Path", style="white", overflow="fold")
        table.add_column("Source", style="green", overflow="fold")
        table.add_column("Publisher", style="yellow", overflow="fold")
        table.add_column("Indicator", style="red", overflow="fold")

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
        summary.add_column(style="bold cyan")
        summary.add_column(justify="right", style="white")
        summary.add_row("Total startup entries", str(analysis.total_entries))
        summary.add_row("Registry entries", str(len(analysis.registry_entries)))
        summary.add_row("Folder entries", str(len(analysis.folder_entries)))
        summary.add_row("Scheduled tasks", str(len(analysis.scheduled_tasks)))

        self.console.print(
            Panel(
                summary,
                title="Summary",
                border_style="green",
                width=min(terminal_width(), 110),
            )
        )
        self.console.print()

    def _message(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            Panel(
                message,
                title=title,
                border_style=style,
                width=min(terminal_width(), 100),
            )
        )
        self.console.print()
        self._wait_for_back()

    def _wait_for_back(self) -> None:
        Prompt.ask("[bold cyan]Press Enter to return[/bold cyan]", default="")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()
