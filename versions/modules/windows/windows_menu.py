from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

from modules.windows.startup_analyzer.startup_menu import StartupAnalyzerPage
from modules.windows.system_info.system_menu import SystemInfoDashboardPage
from settings import SettingsStore
from utils import clear_console


class WindowsMenu:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                "[bold cyan]Select[/bold cyan]",
                choices=["1", "2", "3"],
                show_choices=False,
            )
            if choice == "1":
                StartupAnalyzerPage(self.console, self.settings_store).open()
            elif choice == "2":
                SystemInfoDashboardPage(self.console, self.settings_store).open()
            elif choice == "3":
                return

    def _render(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

        self.console.print()
        self.console.print(Rule("Windows Tools", style="blue"))
        self.console.print()

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right", style="bold cyan")
        table.add_column(style="white")
        table.add_row("[1]", "Startup Analyzer")
        table.add_row("[2]", "System Info Dashboard")
        table.add_row("[3]", "Back")

        self.console.print(Panel(table, border_style="blue", box=box.ROUNDED))
        self.console.print()
