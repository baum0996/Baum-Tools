from __future__ import annotations

import logging

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from modules.utilities.performance_inspector.performance_inspector import (
    GpuLoad,
    PerformanceInspector,
    PerformanceReport,
    ProcessLoad,
)
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
)
from utils import clear_console


class PerformanceInspectorPage:
    def __init__(self, console: Console, settings_store: SettingsStore) -> None:
        self.console = console
        self.settings_store = settings_store
        self.inspector = PerformanceInspector()
        self._logger = logging.getLogger(__name__)

    def open(self) -> None:
        while True:
            self._render_menu()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2", "3", "4", "5"],
                show_choices=False,
            )
            if choice == "1":
                self._run_inspection("all")
            elif choice == "2":
                self._run_inspection("cpu")
            elif choice == "3":
                self._run_inspection("ram")
            elif choice == "4":
                self._run_inspection("gpu")
            elif choice == "5":
                return

    def _render_menu(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Performance Inspector"))
        self.console.print(
            crt_message(
                "Read Only",
                "This tool only analyzes and explains. It does not kill processes, "
                "change services, edit startup items, or modify security settings.",
            )
        )
        self.console.print()
        self.console.print(
            crt_menu(
                "Performance Inspector",
                (
                    ("1", "Full Inspection"),
                    ("2", "CPU Inspection"),
                    ("3", "RAM Inspection"),
                    ("4", "GPU Inspection"),
                    ("5", "Back"),
                ),
            )
        )
        self.console.print(crt_footer("Utilities", "PRESS 5 TO GO BACK"))
        self.console.print()

    def _run_inspection(self, mode: str) -> None:
        self._clear_if_enabled()
        try:
            with Progress(
                SpinnerColumn(style=CRT_GREEN),
                TextColumn(f"[{CRT_GREEN}]Sampling system load...[/{CRT_GREEN}]"),
                transient=True,
                console=self.console,
            ) as progress:
                progress.add_task("Sampling system load...", total=None)
                report = self.inspector.inspect(mode)
        except Exception as exc:
            self._logger.exception("Performance inspection failed.")
            self._message("Performance Inspector", str(exc), CRT_DANGER)
            return

        self._render_report(report)

    def _render_report(self, report: PerformanceReport, wait: bool = True) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Performance Report"))
        self.console.print(self._summary_panel(report))
        self.console.print()

        if report.cpu_processes:
            self._render_process_table("Top CPU Consumers", report.cpu_processes, "cpu")
            self._render_process_explanations("CPU Findings", report.cpu_processes)
        if report.ram_processes:
            self._render_process_table("Top RAM Consumers", report.ram_processes, "ram")
            self._render_process_explanations("RAM Findings", report.ram_processes)
        if report.mode in {"all", "gpu"}:
            self._render_gpu(report.gpu)

        self.console.print(self._global_guidance(report))
        self.console.print(crt_footer("Utilities", "PRESS ENTER TO GO BACK"))
        self.console.print()
        if wait:
            self._wait_for_back()

    def _summary_panel(self, report: PerformanceReport) -> Table:
        table = crt_data_table("System Load", show_header=False)
        table.add_column("Metric", style=f"bold {CRT_GREEN}")
        table.add_column("Value", style=CRT_MUTED)
        table.add_row("Mode", report.mode.upper())
        table.add_row("CPU Total", f"{report.cpu_total_percent:.1f}%")
        table.add_row(
            "RAM Total",
            f"{report.ram_total_percent:.1f}% "
            f"({report.ram_used_gb:.1f}/{report.ram_total_gb:.1f} GB)",
        )
        if report.gpu.available and report.gpu.utilization_percent is not None:
            table.add_row("GPU Total", f"{report.gpu.utilization_percent:.1f}%")
        return table

    def _render_process_table(
        self,
        title: str,
        processes: list[ProcessLoad],
        _metric: str,
    ) -> None:
        table = crt_data_table(title)
        table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
        table.add_column("Process", style=CRT_GREEN, overflow="fold")
        table.add_column("PID", justify="right", style=CRT_MUTED)
        table.add_column("CPU", justify="right", style=CRT_MUTED)
        table.add_column("RAM", justify="right", style=CRT_MUTED)
        table.add_column("Main Signal", style=CRT_WARNING, overflow="fold")

        filtered = [
            process
            for process in processes
            if process.cpu_percent >= 0.1 or process.memory_mb >= 50
        ]
        for index, process in enumerate(filtered[:10], start=1):
            signal = process.risk_notes[0] if process.risk_notes else "-"
            table.add_row(
                str(index).zfill(2),
                process.name,
                str(process.pid),
                f"{process.cpu_percent:.1f}%",
                f"{process.memory_mb:.1f} MB",
                signal,
            )

        if not filtered:
            table.add_row("-", "No significant process found", "-", "-", "-", "-")

        self.console.print(table)
        self.console.print()

    def _render_process_explanations(
        self,
        title: str,
        processes: list[ProcessLoad],
    ) -> None:
        table = crt_data_table(title)
        table.add_column("Process", style=f"bold {CRT_GREEN}", overflow="fold")
        table.add_column("Could Be", style=CRT_MUTED, overflow="fold")
        table.add_column("Prevention", style=CRT_MUTED, overflow="fold")
        table.add_column("Virus?", style=CRT_WARNING, overflow="fold")

        notable = [
            process
            for process in processes
            if process.cpu_percent >= 5 or process.memory_mb >= 500
        ][:6]
        if not notable:
            table.add_row(
                "System",
                "No strong offender in this sample.",
                "Run a full inspection while the slowdown is happening.",
                "No suspicious indicator from this short sample.",
            )
        for process in notable:
            table.add_row(
                process.name,
                "\n".join(process.risk_notes[:3]),
                "\n".join(process.prevention_tips[:3]),
                self._virus_hint(process),
            )

        self.console.print(table)
        self.console.print()

    def _render_gpu(self, gpu: GpuLoad) -> None:
        table = crt_data_table("GPU")
        table.add_column("Metric", style=f"bold {CRT_GREEN}")
        table.add_column("Value", style=CRT_MUTED, overflow="fold")
        if not gpu.available:
            table.add_row("Status", gpu.message)
            table.add_row("Prevention", "Install GPU vendor tools or check Task Manager GPU tab.")
        else:
            table.add_row("Status", gpu.message)
            table.add_row(
                "Utilization",
                f"{gpu.utilization_percent:.1f}%"
                if gpu.utilization_percent is not None
                else "Unknown",
            )
            if gpu.memory_used_mb is not None and gpu.memory_total_mb is not None:
                table.add_row("VRAM", f"{gpu.memory_used_mb}/{gpu.memory_total_mb} MB")
            if gpu.processes:
                for pid, process_name, memory_mb in gpu.processes[:8]:
                    table.add_row(
                        f"PID {pid}",
                        f"{process_name} using {memory_mb} MB VRAM",
                    )
            else:
                table.add_row("GPU Processes", "No compute processes reported.")

        self.console.print(table)
        self.console.print()

    def _global_guidance(self, report: PerformanceReport) -> Table:
        table = crt_data_table("Safe Next Steps")
        table.add_column("#", justify="right", style=f"bold {CRT_GREEN}")
        table.add_column("Recommendation", style=CRT_MUTED, overflow="fold")
        tips = [
            "Watch the same process for 2-5 minutes. Short spikes are normal.",
            "If a browser is high, close heavy tabs and disable suspicious extensions.",
            "If a security tool is high, let the scan finish or schedule scans for idle time.",
            "If a Windows service host is high, inspect the linked service before changing it.",
            "If an unknown executable runs from Temp/AppData and stays high, scan it with security tools.",
            "This tool is text-only and read-only; it intentionally does not terminate anything.",
        ]
        if report.cpu_total_percent >= 80:
            tips.insert(0, "CPU is very high. Save work before closing heavy applications.")
        if report.ram_total_percent >= 85:
            tips.insert(0, "RAM pressure is high. Close unused apps to avoid system slowdown.")
        for index, tip in enumerate(tips[:8], start=1):
            table.add_row(str(index).zfill(2), tip)
        return table

    def _virus_hint(self, process: ProcessLoad) -> str:
        path = process.executable.casefold()
        command = process.command_line.casefold()
        suspicious = (
            "\\temp\\" in path
            or "\\appdata\\local\\temp\\" in path
            or "-encodedcommand" in command
            or "powershell -w hidden" in command
        )
        if suspicious:
            return "Possible. Verify the file path and scan the file."
        if process.name.casefold() in {"system", "registry"}:
            return "Unlikely from this sample."
        return "Not proven. High usage alone does not mean malware."

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
