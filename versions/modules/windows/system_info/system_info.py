from __future__ import annotations

import os
import platform
import socket
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import psutil


@dataclass(frozen=True, slots=True)
class OSInfo:
    version: str
    build_number: str
    architecture: str


@dataclass(frozen=True, slots=True)
class HardwareInfo:
    cpu_model: str
    physical_cores: int
    logical_threads: int
    total_ram: str
    available_ram: str


@dataclass(frozen=True, slots=True)
class DriveInfo:
    name: str
    file_system: str
    total_space: str
    free_space: str


@dataclass(frozen=True, slots=True)
class PythonEnvironmentInfo:
    version: str
    executable: str
    virtual_environment: str


@dataclass(frozen=True, slots=True)
class NetworkInfo:
    hostname: str
    local_ip: str


@dataclass(frozen=True, slots=True)
class SystemInfoSnapshot:
    os_info: OSInfo
    hardware: HardwareInfo
    drives: list[DriveInfo] = field(default_factory=list)
    python_environment: PythonEnvironmentInfo = field(
        default_factory=lambda: PythonEnvironmentInfo("", "", "")
    )
    network: NetworkInfo = field(default_factory=lambda: NetworkInfo("", ""))
    collected_at: datetime = field(default_factory=datetime.now)


class SystemInfoCollector:
    def collect(self) -> SystemInfoSnapshot:
        return SystemInfoSnapshot(
            os_info=self._collect_os_info(),
            hardware=self._collect_hardware_info(),
            drives=self._collect_storage_info(),
            python_environment=self._collect_python_environment(),
            network=self._collect_network_info(),
        )

    @staticmethod
    def _collect_os_info() -> OSInfo:
        windows_version = platform.platform(terse=True)
        build_number = platform.version()
        architecture = platform.machine() or platform.architecture()[0]
        return OSInfo(
            version=windows_version,
            build_number=build_number,
            architecture=architecture,
        )

    @staticmethod
    def _collect_hardware_info() -> HardwareInfo:
        memory = psutil.virtual_memory()
        return HardwareInfo(
            cpu_model=platform.processor() or "Not available",
            physical_cores=psutil.cpu_count(logical=False) or 0,
            logical_threads=psutil.cpu_count(logical=True) or 0,
            total_ram=format_bytes(memory.total),
            available_ram=format_bytes(memory.available),
        )

    @staticmethod
    def _collect_storage_info() -> list[DriveInfo]:
        drives: list[DriveInfo] = []
        for partition in psutil.disk_partitions(all=False):
            if not partition.device:
                continue
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except OSError:
                continue
            drives.append(
                DriveInfo(
                    name=partition.device,
                    file_system=partition.fstype or "Unknown",
                    total_space=format_bytes(usage.total),
                    free_space=format_bytes(usage.free),
                )
            )
        return drives

    @staticmethod
    def _collect_python_environment() -> PythonEnvironmentInfo:
        venv_path = Path.cwd() / ".venv"
        active_venv = os.environ.get("VIRTUAL_ENV", "")
        if active_venv:
            status = f"Active ({active_venv})"
        elif venv_path.exists():
            status = "Detected"
        else:
            status = "Not detected"
        return PythonEnvironmentInfo(
            version=sys.version.split()[0],
            executable=sys.executable,
            virtual_environment=status,
        )

    @staticmethod
    def _collect_network_info() -> NetworkInfo:
        hostname = socket.gethostname()
        return NetworkInfo(
            hostname=hostname,
            local_ip=get_local_ip(hostname),
        )


def get_local_ip(hostname: str) -> str:
    try:
        ip_address = socket.gethostbyname(hostname)
    except OSError:
        return "Not available"

    if ip_address.startswith("127."):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect(("8.8.8.8", 80))
                ip_address = probe.getsockname()[0]
        except OSError:
            return "Not available"

    return ip_address


def format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
