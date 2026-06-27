from __future__ import annotations

import logging

from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from modules.windows.system_info.system_info import (
    SystemInfoCollector,
    SystemInfoSnapshot,
)
from settings import SettingsStore
from ui_theme import (
    CRT_DANGER,
    CRT_GREEN,
    CRT_MUTED,
    CRT_PROMPT,
    crt_data_table,
    crt_footer,
    crt_header,
    crt_message,
)
from utils import clear_console


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
            self._message("System Info Dashboard", str(exc), CRT_DANGER)
            return

        self._render(snapshot)
        self._wait_for_back()

    def _render(self, snapshot: SystemInfoSnapshot) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("System Info Dashboard"))
        self.console.print(
            crt_message("Info", "Read-only Windows system information overview.")
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
        table = Table(title="STORAGE OVERVIEW", box=box.SQUARE, border_style=CRT_GREEN)
        table.add_column("Drive", style=f"bold {CRT_GREEN}", no_wrap=True)
        table.add_column("File System", style=CRT_GREEN)
        table.add_column("Total Space", justify="right", style=CRT_MUTED)
        table.add_column("Free Space", justify="right", style=CRT_MUTED)

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
            crt_message(
                "Footer",
                f"Information collected at {timestamp}",
                CRT_GREEN,
            )
        )
        self.console.print(crt_footer("Windows", "PRESS ENTER TO GO BACK"))
        self.console.print()

    @staticmethod
    def _info_table(title: str) -> Table:
        table = crt_data_table(title)
        table.add_column("Field", style=f"bold {CRT_GREEN}", no_wrap=True)
        table.add_column("Value", style=CRT_MUTED, overflow="fold")
        return table

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
