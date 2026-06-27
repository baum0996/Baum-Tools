from __future__ import annotations

import logging

from rich.console import Console
from rich.prompt import Prompt

from filepicker import FilePicker
from modules.minecraft.texture_pack_scanner import TexturePackScannerPage
from settings import SettingsStore
from ui_theme import CRT_PROMPT, crt_footer, crt_header, crt_menu
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
                f"{CRT_PROMPT} SELECT",
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
        self.console.print(crt_header("Minecraft Tools"))
        self.console.print()
        self.console.print(
            crt_menu("Minecraft Tools", (("1", "Texture Pack Scanner"), ("2", "Back")))
        )
        self.console.print(crt_footer("Minecraft", "PRESS 2 TO GO BACK"))
        self.console.print()
