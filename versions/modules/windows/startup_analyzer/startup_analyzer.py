from __future__ import annotations

import csv
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

if sys.platform == "win32":
    import winreg
else:
    winreg = None


REGISTRY_RUN_KEYS = (
    (
        "HKCU",
        r"Software\Microsoft\Windows\CurrentVersion\Run",
    ),
    (
        "HKLM",
        r"Software\Microsoft\Windows\CurrentVersion\Run",
    ),
    (
        "HKCU",
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
    ),
    (
        "HKLM",
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
    ),
)

UNUSUAL_PATH_MARKERS = (
    "\\appdata\\local\\temp\\",
    "\\windows\\temp\\",
    "\\downloads\\",
)


@dataclass(frozen=True, slots=True)
class StartupEntry:
    name: str
    file_path: str
    source: str
    publisher: str = ""
    indicator: str = ""


@dataclass(frozen=True, slots=True)
class StartupAnalysis:
    registry_entries: list[StartupEntry] = field(default_factory=list)
    folder_entries: list[StartupEntry] = field(default_factory=list)
    scheduled_tasks: list[StartupEntry] = field(default_factory=list)

    @property
    def total_entries(self) -> int:
        return (
            len(self.registry_entries)
            + len(self.folder_entries)
            + len(self.scheduled_tasks)
        )


class StartupAnalyzer:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def scan(self) -> StartupAnalysis:
        if sys.platform != "win32":
            raise RuntimeError("Startup Analyzer is only available on Windows.")

        registry_entries = self._scan_registry_entries()
        folder_entries = self._scan_startup_folders()
        scheduled_tasks = self._scan_scheduled_tasks()

        return StartupAnalysis(
            registry_entries=registry_entries,
            folder_entries=folder_entries,
            scheduled_tasks=scheduled_tasks,
        )

    def _scan_registry_entries(self) -> list[StartupEntry]:
        entries: list[StartupEntry] = []
        if winreg is None:
            return entries

        for hive_name, key_path in REGISTRY_RUN_KEYS:
            hive = (
                winreg.HKEY_CURRENT_USER
                if hive_name == "HKCU"
                else winreg.HKEY_LOCAL_MACHINE
            )
            access_modes = [winreg.KEY_READ]
            if hive_name == "HKLM":
                access_modes.append(winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
                access_modes.append(winreg.KEY_READ | winreg.KEY_WOW64_32KEY)

            for access_mode in access_modes:
                entries.extend(
                    self._read_registry_key(hive, hive_name, key_path, access_mode)
                )

        return self._deduplicate(entries)

    def _read_registry_key(
        self,
        hive: int,
        hive_name: str,
        key_path: str,
        access_mode: int,
    ) -> list[StartupEntry]:
        entries: list[StartupEntry] = []
        if winreg is None:
            return entries

        try:
            with winreg.OpenKey(hive, key_path, 0, access_mode) as key:
                value_count = winreg.QueryInfoKey(key)[1]
                for index in range(value_count):
                    name, command, _value_type = winreg.EnumValue(key, index)
                    command_text = str(command)
                    file_path = extract_executable_path(command_text)
                    entries.append(
                        StartupEntry(
                            name=name,
                            file_path=file_path or command_text,
                            source=f"Registry ({hive_name}\\{key_path})",
                            publisher=get_publisher(file_path),
                            indicator=heuristic_indicator(file_path or command_text),
                        )
                    )
        except FileNotFoundError:
            return entries
        except OSError:
            self._logger.exception("Failed to read registry startup key.")
        return entries

    def _scan_startup_folders(self) -> list[StartupEntry]:
        entries: list[StartupEntry] = []
        for folder_name, folder in startup_folders():
            if not folder.exists():
                continue
            try:
                for path in folder.iterdir():
                    if path.is_file():
                        entries.append(
                            StartupEntry(
                                name=path.name,
                                file_path=str(path),
                                source=f"Folder ({folder_name})",
                                publisher=get_publisher(str(path)),
                                indicator=heuristic_indicator(str(path)),
                            )
                        )
            except OSError:
                self._logger.exception("Failed to read startup folder.")
        return entries

    def _scan_scheduled_tasks(self) -> list[StartupEntry]:
        entries = self._scan_scheduled_tasks_with_powershell()
        if entries:
            return entries
        return self._scan_scheduled_tasks_with_schtasks()

    def _scan_scheduled_tasks_with_powershell(self) -> list[StartupEntry]:
        command = (
            "$tasks = Get-ScheduledTask | Where-Object { "
            "$_.Triggers -and ($_.Triggers.CimClass.CimClassName -contains "
            "'MSFT_TaskBootTrigger' -or $_.Triggers.CimClass.CimClassName -contains "
            "'MSFT_TaskLogonTrigger') }; "
            "$tasks | ForEach-Object { "
            "[PSCustomObject]@{ "
            "TaskName = $_.TaskName; "
            "TaskPath = $_.TaskPath; "
            "Action = (($_.Actions | ForEach-Object { "
            "($_.Execute + ' ' + $_.Arguments).Trim() }) -join '; ') "
            "} } | ConvertTo-Json -Depth 4"
        )

        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.SubprocessError):
            self._logger.exception("Failed to query scheduled tasks through PowerShell.")
            return []

        if completed.returncode != 0 or not completed.stdout.strip():
            return []

        return parse_powershell_scheduled_tasks(completed.stdout)

    def _scan_scheduled_tasks_with_schtasks(self) -> list[StartupEntry]:
        try:
            completed = subprocess.run(
                ["schtasks", "/Query", "/FO", "CSV", "/V"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.SubprocessError):
            self._logger.exception("Failed to query scheduled tasks.")
            return []

        if completed.returncode != 0 or not completed.stdout.strip():
            return []

        return parse_scheduled_tasks(completed.stdout)

    @staticmethod
    def _deduplicate(entries: Iterable[StartupEntry]) -> list[StartupEntry]:
        seen: set[tuple[str, str, str]] = set()
        deduplicated: list[StartupEntry] = []
        for entry in entries:
            key = (entry.name.lower(), entry.file_path.lower(), entry.source.lower())
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(entry)
        return deduplicated


def startup_folders() -> list[tuple[str, Path]]:
    app_data = os.environ.get("APPDATA", "")
    program_data = os.environ.get("PROGRAMDATA", "")
    return [
        (
            "Current User",
            Path(app_data)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup",
        ),
        (
            "All Users",
            Path(program_data)
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup",
        ),
    ]


def parse_scheduled_tasks(output: str) -> list[StartupEntry]:
    entries: list[StartupEntry] = []
    reader = csv.DictReader(output.splitlines())
    for row in reader:
        schedule_type = normalized_field(row, "Schedule Type")
        task_to_run = normalized_field(row, "Task To Run")
        task_name = normalized_field(row, "TaskName") or normalized_field(row, "Task Name")

        if not is_startup_related_task(schedule_type):
            continue

        file_path = extract_executable_path(task_to_run) or task_to_run
        entries.append(
            StartupEntry(
                name=task_name or "Unnamed scheduled task",
                file_path=file_path or "Not available",
                source="Task Scheduler",
                publisher=get_publisher(file_path),
                indicator=heuristic_indicator(file_path or task_to_run),
            )
        )
    return entries


def parse_powershell_scheduled_tasks(output: str) -> list[StartupEntry]:
    try:
        raw_data = json.loads(output)
    except json.JSONDecodeError:
        return []

    records = raw_data if isinstance(raw_data, list) else [raw_data]
    entries: list[StartupEntry] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        task_name = str(record.get("TaskName") or "Unnamed scheduled task")
        task_path = str(record.get("TaskPath") or "\\")
        action = str(record.get("Action") or "")
        file_path = extract_executable_path(action) or action or "Not available"

        entries.append(
            StartupEntry(
                name=f"{task_path}{task_name}",
                file_path=file_path,
                source="Task Scheduler",
                publisher=get_publisher(file_path),
                indicator=heuristic_indicator(file_path or action),
            )
        )

    return entries


def normalized_field(row: dict[str, str], field_name: str) -> str:
    for key, value in row.items():
        if key.strip().lower() == field_name.lower():
            return value.strip()
    return ""


def is_startup_related_task(schedule_type: str) -> bool:
    normalized = schedule_type.lower()
    return any(marker in normalized for marker in ("logon", "startup", "boot"))


def extract_executable_path(command: str) -> str:
    expanded = os.path.expandvars(command).strip()
    if not expanded:
        return ""

    quoted_match = re.match(r'^"([^"]+)"', expanded)
    if quoted_match:
        return quoted_match.group(1)

    executable_match = re.search(
        r"([A-Za-z]:\\[^\s]+?\.(?:exe|dll|bat|cmd|ps1|vbs|js|jar|msi|scr|com|lnk))",
        expanded,
        flags=re.IGNORECASE,
    )
    if executable_match:
        return executable_match.group(1)

    parts = expanded.split()
    return parts[0] if parts else ""


@lru_cache(maxsize=512)
def get_publisher(file_path: str) -> str:
    if not file_path or not Path(file_path).exists():
        return ""

    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                (
                    "$signature = Get-AuthenticodeSignature -LiteralPath "
                    f"'{escape_powershell_literal(file_path)}'; "
                    "$signature.SignerCertificate.Subject"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    if completed.returncode != 0:
        return ""
    return normalize_publisher(completed.stdout.strip())


def escape_powershell_literal(value: str) -> str:
    return value.replace("'", "''")


def normalize_publisher(subject: str) -> str:
    if not subject:
        return ""
    common_name_match = re.search(r"(?:^|,\s*)CN=([^,]+)", subject)
    if common_name_match:
        return common_name_match.group(1).strip()
    return subject


def heuristic_indicator(path_text: str) -> str:
    normalized = path_text.lower()
    if any(marker in normalized for marker in UNUSUAL_PATH_MARKERS):
        return "Unusual entry (heuristic indicator)"
    return ""
