from __future__ import annotations

import logging
import platform
import sys
import time
from importlib import metadata
from typing import Callable

from rich.align import Align
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from constants import (
    APP_DESCRIPTION,
    APP_DEVELOPER,
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    ASSETS_DIR,
    LOGS_DIR,
    MENU_OPTIONS,
    THEMES,
)
from filepicker import FilePicker
from modules.discord.discord_menu import DiscordMenu
from modules.minecraft.minecraft_menu import MinecraftMenu
from modules.utilities.utilities_menu import UtilitiesMenu
from modules.windows.windows_menu import WindowsMenu
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
from utils import clear_console, ensure_directories, format_bool, terminal_width


class BaumToolsApp:
    def __init__(self, settings_store: SettingsStore) -> None:
        self.console = Console()
        self.settings_store = settings_store
        self.file_picker = FilePicker()
        self.running = True
        self._logger = logging.getLogger(__name__)
        ensure_directories([ASSETS_DIR, LOGS_DIR])

    def run(self) -> None:
        self._logger.info("Application started.")
        self._launch_sequence()
        while self.running:
            self._render_main_menu()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=list(MENU_OPTIONS.keys()),
                show_choices=False,
            )
            self._handle_menu_choice(choice)

    def _handle_menu_choice(self, choice: str) -> None:
        actions: dict[str, Callable[[], None]] = {
            "1": self._minecraft_menu,
            "2": self._windows_menu,
            "3": self._discord_menu,
            "4": lambda: self._future_category("Network"),
            "5": lambda: self._future_category("File Tools"),
            "6": self._utilities_menu,
            "7": self._settings_page,
            "8": self._about_page,
            "9": self._exit,
        }
        actions[choice]()

    def _render_main_menu(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Main Menu"))
        self.console.print()
        self.console.print(crt_menu("Main Menu", MENU_OPTIONS.items()))
        self.console.print(crt_footer("Main Menu", "PRESS 1-9 + ENTER"))
        self.console.print()

    def _launch_sequence(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

        if self.settings_store.settings.animations:
            steps = (
                "INITIALIZING",
                "LOADING MODULES",
                "PREPARING INTERFACE",
                "SYSTEM CHECK",
                "READY",
            )
            for index, step in enumerate(steps, start=1):
                self._clear_if_enabled()
                self.console.print()
                self.console.print(self._startup_panel(step, index, len(steps)))
                time.sleep(0.22)

        self._clear_if_enabled()
        self.console.print()
        self.console.print(self._start_screen())
        self.console.print()
        Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO CONTINUE", default="")

    def _startup_panel(self, active_step: str, index: int, total: int) -> object:
        status = Table.grid(padding=(0, 2))
        status.add_column(justify="right", style=CRT_MUTED)
        status.add_column(style=CRT_GREEN)
        for step in (
            "INITIALIZING",
            "LOADING MODULES",
            "PREPARING INTERFACE",
            "SYSTEM CHECK",
            "READY",
        ):
            marker = "######" if step == active_step else "......"
            status.add_row(step, marker)

        logo = Text()
        logo.append(f"\n{APP_NAME}\n", style=f"bold {CRT_GREEN}")
        logo.append(f"\nBOOT SEQUENCE {index}/{total}", style=CRT_MUTED)

        body = Table.grid(expand=True)
        body.add_column(ratio=1)
        body.add_column(justify="center", ratio=2)
        body.add_row(status, Align.center(logo))
        return crt_panel(body, "Launch", width=min(terminal_width(), 112))

    def _start_screen(self) -> object:
        logo = Text()
        logo.append("\n")
        logo.append(f"{APP_NAME}\n", style=f"bold {CRT_GREEN}")
        logo.append(APP_SUBTITLE.upper(), style=CRT_MUTED)
        logo.append("\n\n[ PRESS ENTER TO CONTINUE ]", style=CRT_GREEN)

        info = Table.grid(expand=True)
        info.add_column(style=CRT_MUTED)
        info.add_column(justify="right", style=CRT_MUTED)
        info.add_row(f"VERSION: {APP_VERSION}", "STATUS: READY")
        info.add_row("SYSTEM: WINDOWS", "(C) 2026 BAUM TOOLS")

        body = Table.grid(expand=True)
        body.add_column()
        body.add_row(Align.center(logo))
        body.add_row("")
        body.add_row(info)
        return crt_panel(body, "BAUM TOOLS V1", width=min(terminal_width(), 112))

    def _minecraft_menu(self) -> None:
        MinecraftMenu(self.console, self.settings_store, self.file_picker).open()

    def _windows_menu(self) -> None:
        WindowsMenu(self.console, self.settings_store).open()

    def _discord_menu(self) -> None:
        DiscordMenu(self.console, self.settings_store).open()

    def _utilities_menu(self) -> None:
        UtilitiesMenu(self.console, self.settings_store).open()

    def _settings_page(self) -> None:
        while True:
            self._clear_if_enabled()
            settings = self.settings_store.settings

            table = crt_data_table("Settings")
            table.add_column("Key", style=f"bold {CRT_GREEN}", no_wrap=True)
            table.add_column("Setting", style=CRT_MUTED)
            table.add_column("Value", style=CRT_GREEN)
            table.add_row("01", "Theme", settings.theme)
            table.add_row("02", "Animations", format_bool(settings.animations))
            table.add_row(
                "03",
                "Auto Clear Console",
                format_bool(settings.auto_clear_console),
            )
            table.add_row("04", "Scan Hidden Files", format_bool(settings.scan_hidden_files))
            table.add_row("05", "Show File Sizes", format_bool(settings.show_file_sizes))
            table.add_row(
                "06",
                "Confirm Before Exit",
                format_bool(settings.confirm_before_exit),
            )
            table.add_row("00", "Back", "Return to main menu")

            self.console.print()
            self.console.print(crt_header("Settings"))
            self.console.print(table)
            self.console.print(crt_footer("Settings", "PRESS 0 TO GO BACK"))
            self.console.print()

            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT SETTING",
                choices=["0", "1", "2", "3", "4", "5", "6"],
                show_choices=False,
            )
            if choice == "0":
                return
            if choice == "1":
                self._cycle_theme()
                continue

            key_map = {
                "2": "animations",
                "3": "auto_clear_console",
                "4": "scan_hidden_files",
                "5": "show_file_sizes",
                "6": "confirm_before_exit",
            }
            try:
                self.settings_store.toggle(key_map[choice])
            except (KeyError, TypeError, OSError) as exc:
                self._logger.exception("Failed to update setting.")
                self._message_page("Settings Error", str(exc), CRT_DANGER)

    def _cycle_theme(self) -> None:
        current_theme = self.settings_store.settings.theme
        try:
            index = THEMES.index(current_theme)
        except ValueError:
            index = 0
        next_theme = THEMES[(index + 1) % len(THEMES)]
        self.settings_store.set_theme(next_theme)

    def _about_page(self) -> None:
        self._clear_if_enabled()

        table = crt_data_table("About", show_header=False)
        table.add_column("Name", style=f"bold {CRT_GREEN}", no_wrap=True)
        table.add_column("Value", style=CRT_MUTED)
        table.add_row("Version", APP_VERSION)
        table.add_row("Python Version", sys.version.split()[0])
        table.add_row("Operating System", f"{platform.system()} {platform.release()}")
        table.add_row("Developer", APP_DEVELOPER)
        table.add_row("Description", APP_DESCRIPTION)
        table.add_row("Installed Modules", self._installed_modules())

        self.console.print()
        self.console.print(crt_header("About"))
        self.console.print(table)
        self.console.print(crt_footer("About", "PRESS ENTER TO GO BACK"))
        self.console.print()
        self._wait_for_back()

    def _future_category(self, title: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            crt_panel(
                "Coming in a future update.",
                title=title,
                border_style=CRT_WARNING,
                width=min(terminal_width(), 100),
            )
        )
        self.console.print()
        self._wait_for_back()

    def _message_page(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self._run_transition(f"{title}...")
        self.console.print()
        self.console.print(crt_message(title, message, style))
        self.console.print()
        self._wait_for_back()

    def _exit(self) -> None:
        if self.settings_store.settings.confirm_before_exit:
            if not Confirm.ask(f"[bold {CRT_WARNING}]Exit BAUM TOOLS V1?[/bold {CRT_WARNING}]"):
                return

        self._logger.info("Application exited.")
        self.running = False
        self._clear_if_enabled()
        self.console.print(f"[bold {CRT_GREEN}]GOODBYE.[/bold {CRT_GREEN}]")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

    def _run_transition(self, message: str) -> None:
        if not self.settings_store.settings.animations:
            return

        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn(f"[{CRT_GREEN}]{{task.description}}[/{CRT_GREEN}]"),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task(message, total=None)
            progress.update(task)

    def _wait_for_back(self) -> None:
        Prompt.ask(f"{CRT_PROMPT} PRESS ENTER TO RETURN", default="")

    @staticmethod
    def _installed_modules() -> str:
        modules = ["rich", "colorama"]
        versions: list[str] = []
        for module in modules:
            try:
                versions.append(f"{module} {metadata.version(module)}")
            except metadata.PackageNotFoundError:
                versions.append(f"{module} not installed")
        return ", ".join(versions)
