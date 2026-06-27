from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from modules.windows.startup_analyzer.startup_menu import StartupAnalyzerPage
from modules.windows.system_info.system_menu import SystemInfoDashboardPage
from settings import SettingsStore
from ui_theme import CRT_PROMPT, crt_footer, crt_header, crt_menu
from utils import clear_console


class WindowsMenu:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
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
        self.console.print(crt_header("Windows Tools"))
        self.console.print()
        self.console.print(
            crt_menu(
                "Windows Tools",
                (
                    ("1", "Startup Analyzer"),
                    ("2", "System Info Dashboard"),
                    ("3", "Back"),
                ),
            )
        )
        self.console.print(crt_footer("Windows", "PRESS 3 TO GO BACK"))
        self.console.print()
