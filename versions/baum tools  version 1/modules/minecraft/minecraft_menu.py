from __future__ import annotations

import logging

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

from filepicker import FilePicker
from modules.minecraft.texture_pack_scanner import TexturePackScannerPage
from settings import SettingsStore
from utils import clear_console


class MinecraftMenu:
    def __init__(
        self,
        console: Console,
        settings_store: SettingsStore,
        file_picker: FilePicker,
    ) -> None:
        self.console = console
        self.settings_store = settings_store
        self.file_picker = file_picker
        self._logger = logging.getLogger(__name__)

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                "[bold cyan]Select[/bold cyan]",
                choices=["1", "2"],
                show_choices=False,
            )
            if choice == "1":
                TexturePackScannerPage(
                    self.console,
                    self.settings_store,
                    self.file_picker,
                ).open()
            elif choice == "2":
                return

    def _render(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

        self.console.print()
        self.console.print(Rule("Minecraft Tools", style="blue"))
        self.console.print()

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right", style="bold cyan")
        table.add_column(style="white")
        table.add_row("[1]", "Texture Pack Scanner")
        table.add_row("[2]", "Back")

        self.console.print(Panel(table, border_style="blue", box=box.ROUNDED))
        self.console.print()
