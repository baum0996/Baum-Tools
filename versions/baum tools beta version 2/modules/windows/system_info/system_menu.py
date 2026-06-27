from __future__ import annotations

import logging

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from modules.windows.system_info.system_info import (
    SystemInfoCollector,
    SystemInfoSnapshot,
)
from settings import SettingsStore
from utils import clear_console, terminal_width


class SystemInfoDashboardPage:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store
        self.collector = SystemInfoCollector()
        self._logger = logging.getLogger(__name__)

    def open(self) -> None:
        self._clear_if_enabled()
        try:
            snapshot = self.collector.collect()
        except Exception as exc:
            self._logger.exception("System information collection failed.")
            self._message("System Info Dashboard", str(exc), "red")
            return

        self._render(snapshot)
        self._wait_for_back()

    def _render(self, snapshot: SystemInfoSnapshot) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(
            Panel(
                "Read-only Windows system information overview.",
                title="System Info Dashboard",
                border_style="cyan",
                width=min(terminal_width(), 110),
            )
        )
        self.console.print()
        self._render_os_info(snapshot)
        self._render_hardware_info(snapshot)
        self._render_storage_overview(snapshot)
        self._render_python_environment(snapshot)
        self._render_network_info(snapshot)
        self._render_footer(snapshot)

    def _render_os_info(self, snapshot: SystemInfoSnapshot) -> None:
        table = self._info_table("OS Information")
        table.add_row("Windows Version", snapshot.os_info.version)
        table.add_row("Build Number", snapshot.os_info.build_number)
        table.add_row("Architecture", snapshot.os_info.architecture)
        self.console.print(table)
        self.console.print()

    def _render_hardware_info(self, snapshot: SystemInfoSnapshot) -> None:
        table = self._info_table("Hardware Information")
        table.add_row("CPU Model", snapshot.hardware.cpu_model)
        table.add_row("Physical Cores", str(snapshot.hardware.physical_cores))
        table.add_row("Logical Threads", str(snapshot.hardware.logical_threads))
        table.add_row("Total RAM", snapshot.hardware.total_ram)
        table.add_row("Available RAM", snapshot.hardware.available_ram)
        self.console.print(table)
        self.console.print()

    def _render_storage_overview(self, snapshot: SystemInfoSnapshot) -> None:
        table = Table(title="Storage Overview", box=box.SIMPLE_HEAVY, border_style="blue")
        table.add_column("Drive", style="bold cyan", no_wrap=True)
        table.add_column("File System", style="green")
        table.add_column("Total Space", justify="right", style="white")
        table.add_column("Free Space", justify="right", style="white")

        if snapshot.drives:
            for drive in snapshot.drives:
                table.add_row(
                    drive.name,
                    drive.file_system,
                    drive.total_space,
                    drive.free_space,
                )
        else:
            table.add_row("No drives found", "-", "-", "-")

        self.console.print(table)
        self.console.print()

    def _render_python_environment(self, snapshot: SystemInfoSnapshot) -> None:
        table = self._info_table("Python Environment")
        table.add_row("Python Version", snapshot.python_environment.version)
        table.add_row("Executable", snapshot.python_environment.executable)
        table.add_row(
            "Virtual Environment",
            snapshot.python_environment.virtual_environment,
        )
        self.console.print(table)
        self.console.print()

    def _render_network_info(self, snapshot: SystemInfoSnapshot) -> None:
        table = self._info_table("Network Information")
        table.add_row("Hostname", snapshot.network.hostname)
        table.add_row("Local IP Address", snapshot.network.local_ip)
        self.console.print(table)
        self.console.print()

    def _render_footer(self, snapshot: SystemInfoSnapshot) -> None:
        timestamp = snapshot.collected_at.strftime("%Y-%m-%d %H:%M:%S")
        self.console.print(
            Panel(
                f"Information collected at {timestamp}",
                border_style="green",
                width=min(terminal_width(), 110),
            )
        )
        self.console.print()

    @staticmethod
    def _info_table(title: str) -> Table:
        table = Table(title=title, box=box.SIMPLE_HEAVY, border_style="blue")
        table.add_column("Field", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="white", overflow="fold")
        return table

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
