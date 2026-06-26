from __future__ import annotations

import logging
from pathlib import Path
from tkinter import Tk, filedialog


class FilePicker:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def select_folder(self) -> Path | None:
        root = self._create_root()
        try:
            selected = filedialog.askdirectory(title="Select Folder")
            return Path(selected) if selected else None
        except Exception:
            self._logger.exception("Folder selection failed.")
            raise
        finally:
            root.destroy()

    def select_file(
        self,
        title: str = "Select File",
        filetypes: list[tuple[str, str]] | None = None,
    ) -> Path | None:
        root = self._create_root()
        try:
            selected = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes or [("All files", "*.*")],
            )
            return Path(selected) if selected else None
        except Exception:
            self._logger.exception("File selection failed.")
            raise
        finally:
            root.destroy()

    @staticmethod
    def _create_root() -> Tk:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        return root
