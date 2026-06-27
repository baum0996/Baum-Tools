from __future__ import annotations

import logging
import platform
import sys
from importlib import metadata
from typing import Callable

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
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
from modules.minecraft.minecraft_menu import MinecraftMenu
from modules.windows.windows_menu import WindowsMenu
from settings import SettingsStore
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
        while self.running:
            self._render_main_menu()
            choice = Prompt.ask(
                "[bold cyan]Select[/bold cyan]",
                choices=list(MENU_OPTIONS.keys()),
                show_choices=False,
            )
            self._handle_menu_choice(choice)

    def _handle_menu_choice(self, choice: str) -> None:
        actions: dict[str, Callable[[], None]] = {
            "1": self._minecraft_menu,
            "2": self._windows_menu,
            "3": lambda: self._future_category("Network"),
            "4": lambda: self._future_category("File Tools"),
            "5": lambda: self._future_category("Utilities"),
            "6": self._settings_page,
            "7": self._about_page,
            "8": self._exit,
        }
        actions[choice]()

    def _render_main_menu(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(Rule(style="blue"))
        self.console.print(
            Align.center(
                Text(
                    f"\n{APP_NAME}\n\n{APP_SUBTITLE}\n\nDeveloped by {APP_DEVELOPER}\n",
                    justify="center",
                    style="bold cyan",
                )
            )
        )
        self.console.print(Rule(style="blue"))
        self.console.print()

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="right", style="bold cyan")
        table.add_column(style="white")
        for key, label in MENU_OPTIONS.items():
            table.add_row(f"[{key}]", label)

        self.console.print(
            Panel(table, title="Categories", border_style="blue", box=box.ROUNDED)
        )
        self.console.print()

    def _minecraft_menu(self) -> None:
        MinecraftMenu(self.console, self.settings_store, self.file_picker).open()

    def _windows_menu(self) -> None:
        WindowsMenu(self.console, self.settings_store).open()

    def _settings_page(self) -> None:
        while True:
            self._clear_if_enabled()
            settings = self.settings_store.settings

            table = Table(
                title="Settings",
                box=box.SIMPLE_HEAVY,
                border_style="blue",
                show_lines=False,
            )
            table.add_column("Key", style="bold cyan", no_wrap=True)
            table.add_column("Setting", style="white")
            table.add_column("Value", style="green")
            table.add_row("1", "Theme", settings.theme)
            table.add_row("2", "Animations", format_bool(settings.animations))
            table.add_row(
                "3",
                "Auto Clear Console",
                format_bool(settings.auto_clear_console),
            )
            table.add_row("4", "Scan Hidden Files", format_bool(settings.scan_hidden_files))
            table.add_row("5", "Show File Sizes", format_bool(settings.show_file_sizes))
            table.add_row(
                "6",
                "Confirm Before Exit",
                format_bool(settings.confirm_before_exit),
            )
            table.add_row("0", "Back", "Return to main menu")

            self.console.print()
            self.console.print(table)
            self.console.print()

            choice = Prompt.ask(
                "[bold cyan]Select setting[/bold cyan]",
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
                self._message_page("Settings Error", str(exc), "red")

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

        table = Table(box=box.SIMPLE_HEAVY, border_style="blue", show_header=False)
        table.add_column("Name", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="white")
        table.add_row("Version", APP_VERSION)
        table.add_row("Python Version", sys.version.split()[0])
        table.add_row("Operating System", f"{platform.system()} {platform.release()}")
        table.add_row("Developer", APP_DEVELOPER)
        table.add_row("Description", APP_DESCRIPTION)
        table.add_row("Installed Modules", self._installed_modules())

        self.console.print()
        self.console.print(Panel.fit(APP_NAME, subtitle="About", border_style="cyan"))
        self.console.print(table)
        self.console.print()
        self._wait_for_back()

    def _future_category(self, title: str) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            Panel(
                "Coming in a future update.",
                title=title,
                border_style="yellow",
                width=min(terminal_width(), 100),
            )
        )
        self.console.print()
        self._wait_for_back()

    def _message_page(self, title: str, message: str, style: str) -> None:
        self._clear_if_enabled()
        self._run_transition(f"{title}...")
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

    def _exit(self) -> None:
        if self.settings_store.settings.confirm_before_exit:
            if not Confirm.ask("[bold yellow]Exit BAUM TOOLS V1?[/bold yellow]"):
                return

        self._logger.info("Application exited.")
        self.running = False
        self._clear_if_enabled()
        self.console.print("[bold green]Goodbye.[/bold green]")

    def _clear_if_enabled(self) -> None:
        if self.settings_store.settings.auto_clear_console:
            clear_console()

    def _run_transition(self, message: str) -> None:
        if not self.settings_store.settings.animations:
            return

        with Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[cyan]{task.description}[/cyan]"),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task(message, total=None)
            progress.update(task)

    def _wait_for_back(self) -> None:
        Prompt.ask("[bold cyan]Press Enter to return[/bold cyan]", default="")

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
