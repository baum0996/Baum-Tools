from __future__ import annotations

import os
import shutil
from pathlib import Path


def clear_console() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def ensure_directories(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def format_bool(value: bool) -> str:
    return "Enabled" if value else "Disabled"


def terminal_width(default: int = 80) -> int:
    return shutil.get_terminal_size((default, 24)).columns
