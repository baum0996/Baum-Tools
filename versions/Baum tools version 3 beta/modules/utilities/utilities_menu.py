from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from modules.utilities.performance_inspector.performance_menu import (
    PerformanceInspectorPage,
)
from settings import SettingsStore
from ui_theme import CRT_PROMPT, crt_footer, crt_header, crt_menu
from utils import clear_console


class UtilitiesMenu:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2"],
                show_choices=False,
            )
            if choice == "1":
                PerformanceInspectorPage(self.console, self.settings_store).open()
            elif choice == "2":
                return

    def _render(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

        self.console.print()
        self.console.print(crt_header("Utilities"))
        self.console.print()
        self.console.print(
            crt_menu(
                "Utilities",
                (
                    ("1", "Performance Inspector"),
                    ("2", "Back"),
                ),
            )
        )
        self.console.print(crt_footer("Utilities", "PRESS 2 TO GO BACK"))
        self.console.print()

