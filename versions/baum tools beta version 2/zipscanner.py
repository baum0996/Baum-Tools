from __future__ import annotations

from pathlib import Path
from zipfile import is_zipfile


class ZipScanner:
    def __init__(self, path: Path) -> None:
        self.path = path

    def is_ready(self) -> bool:
        return self.path.exists() and self.path.is_file() and is_zipfile(self.path)
