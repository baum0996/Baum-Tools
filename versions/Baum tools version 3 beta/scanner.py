from __future__ import annotations

from pathlib import Path


class FolderScanner:
    def __init__(self, root: Path) -> None:
        self.root = root

    def is_ready(self) -> bool:
        return self.root.exists() and self.root.is_dir()
