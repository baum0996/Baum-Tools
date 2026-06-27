from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass, field

import psutil


@dataclass(slots=True)
class ProcessLoad:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    username: str
    executable: str
    command_line: str
    risk_notes: list[str] = field(default_factory=list)
    prevention_tips: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GpuLoad:
    available: bool
    utilization_percent: float | None = None
    memory_used_mb: int | None = None
    memory_total_mb: int | None = None
    processes: list[tuple[int, str, int]] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class PerformanceReport:
    cpu_total_percent: float
    ram_total_percent: float
    ram_used_gb: float
    ram_total_gb: float
    cpu_processes: list[ProcessLoad]
    ram_processes: list[ProcessLoad]
    gpu: GpuLoad
    mode: str


class PerformanceInspector:
    def __init__(self, sample_seconds: float = 1.0) -> None:
        self.sample_seconds = sample_seconds
        self._logger = logging.getLogger(__name__)
        self._cpu_count = psutil.cpu_count() or 1

    def inspect(self, mode: str) -> PerformanceReport:
        normalized_mode = mode.lower()
        self._prime_process_sampling()
        time.sleep(self.sample_seconds)

        cpu_total = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        processes = self._collect_processes()
        gpu = self._collect_gpu_load() if normalized_mode in {"all", "gpu"} else GpuLoad(
            available=False,
            message="GPU scan was not selected.",
        )

        cpu_processes = sorted(
            processes,
            key=lambda process: process.cpu_percent,
            reverse=True,
        )[:12]
        ram_processes = sorted(
            processes,
            key=lambda process: process.memory_mb,
            reverse=True,
        )[:12]

        return PerformanceReport(
            cpu_total_percent=cpu_total,
            ram_total_percent=float(memory.percent),
            ram_used_gb=float(memory.used) / 1024**3,
            ram_total_gb=float(memory.total) / 1024**3,
            cpu_processes=cpu_processes if normalized_mode in {"all", "cpu"} else [],
            ram_processes=ram_processes if normalized_mode in {"all", "ram"} else [],
            gpu=gpu,
            mode=normalized_mode,
        )

    def _prime_process_sampling(self) -> None:
        for process in psutil.process_iter():
            try:
                process.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def _collect_processes(self) -> list[ProcessLoad]:
        processes: list[ProcessLoad] = []
        for process in psutil.process_iter(
            ["pid", "name", "memory_info", "memory_percent", "username", "exe", "cmdline"]
        ):
            try:
                info = process.info
                memory_info = info.get("memory_info")
                command_line = " ".join(info.get("cmdline") or [])
                load = ProcessLoad(
                    pid=int(info.get("pid") or process.pid),
                    name=str(info.get("name") or "Unknown"),
                    cpu_percent=float(process.cpu_percent(interval=None))
                    / self._cpu_count,
                    memory_mb=(memory_info.rss / 1024**2) if memory_info else 0.0,
                    memory_percent=float(info.get("memory_percent") or 0.0),
                    username=str(info.get("username") or "-"),
                    executable=str(info.get("exe") or ""),
                    command_line=command_line,
                )
                load.risk_notes = self._risk_notes(load)
                load.prevention_tips = self._prevention_tips(load)
                processes.append(load)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except OSError:
                self._logger.exception("Failed to inspect process.")
        return processes

    def _collect_gpu_load(self) -> GpuLoad:
        summary = self._run_nvidia_smi(
            [
                "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ]
        )
        if summary is None:
            return GpuLoad(
                available=False,
                message="GPU data is unavailable. NVIDIA nvidia-smi was not found or failed.",
            )

        first_line = summary.splitlines()[0] if summary.splitlines() else ""
        parts = [part.strip() for part in first_line.split(",")]
        gpu = GpuLoad(available=True)
        if len(parts) >= 3:
            gpu.utilization_percent = self._to_float(parts[0])
            gpu.memory_used_mb = self._to_int(parts[1])
            gpu.memory_total_mb = self._to_int(parts[2])

        process_output = self._run_nvidia_smi(
            [
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader,nounits",
            ]
        )
        if process_output:
            for line in process_output.splitlines():
                fields = [field.strip() for field in line.split(",")]
                if len(fields) >= 3:
                    gpu.processes.append(
                        (
                            self._to_int(fields[0]) or 0,
                            fields[1],
                            self._to_int(fields[2]) or 0,
                        )
                    )

        if not gpu.message:
            gpu.message = "GPU data was read in read-only mode."
        return gpu

    def _run_nvidia_smi(self, arguments: list[str]) -> str | None:
        try:
            completed = subprocess.run(
                ["nvidia-smi", *arguments],
                capture_output=True,
                check=False,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.strip()

    def _risk_notes(self, process: ProcessLoad) -> list[str]:
        notes: list[str] = []
        lowered_name = process.name.casefold()
        lowered_path = process.executable.casefold()
        lowered_command = process.command_line.casefold()

        if process.cpu_percent >= 25:
            notes.append("High CPU usage during the sample window.")
        if process.memory_mb >= 1_000:
            notes.append("High RAM usage. This can cause lag or swapping.")
        if any(part in lowered_path for part in ("\\temp\\", "\\appdata\\local\\temp\\")):
            notes.append("Executable is running from a temporary folder.")
        if not process.executable and lowered_name not in {"system", "registry"}:
            notes.append("Executable path is hidden or unavailable.")
        if any(token in lowered_command for token in ("-encodedcommand", "powershell -w hidden")):
            notes.append("Command line contains patterns often used by malware.")
        if lowered_name in {"chrome.exe", "msedge.exe", "firefox.exe"}:
            notes.append("Browser load is often caused by tabs, extensions, or video pages.")
        if "svchost" in lowered_name:
            notes.append("Windows service host. Inspect child service before changing anything.")
        if "discord" in lowered_name or "spotify" in lowered_name:
            notes.append("Background media or overlay features can increase resource use.")
        return notes or ["No obvious suspicious pattern from this text-only inspection."]

    def _prevention_tips(self, process: ProcessLoad) -> list[str]:
        name = process.name.casefold()
        tips: list[str] = []

        if process.cpu_percent >= 15:
            tips.append("Close or restart the app if the spike does not drop after a few minutes.")
        if process.memory_mb >= 1_000:
            tips.append("Reduce open tabs/projects, then restart the app to release memory.")
        if "chrome" in name or "msedge" in name or "firefox" in name:
            tips.append("Disable unnecessary browser extensions and close heavy tabs.")
        if "discord" in name:
            tips.append("Disable hardware acceleration and overlays if Discord keeps spiking.")
        if "spotify" in name:
            tips.append("Disable animated canvas/video features and restart Spotify.")
        if "svchost" in name:
            tips.append("Use Task Manager > Services to identify the service before taking action.")
        if "malwarebytes" in name or "msmpeng" in name:
            tips.append("Let the scan finish or schedule security scans for idle time.")
        if not tips:
            tips.append("Check whether the process is expected. Search the exact file path if unsure.")
        return tips

    @staticmethod
    def _to_float(value: str) -> float | None:
        try:
            return float(value.strip().replace("%", ""))
        except ValueError:
            return None

    @staticmethod
    def _to_int(value: str) -> int | None:
        try:
            return int(float(value.strip().replace("MiB", "")))
        except ValueError:
            return None
