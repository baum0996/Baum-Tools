from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from filepicker import FilePicker
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
    crt_panel,
)
from utils import clear_console


TEXTURE_PACK_EXTENSIONS = {
    ".png": "PNG",
    ".json": "JSON",
    ".ogg": "OGG",
    ".mcmeta": "MCMETA",
    ".properties": "Properties",
    ".txt": "Text files",
}

EXECUTABLE_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".ps1",
    ".vbs",
    ".js",
    ".jar",
    ".msi",
    ".scr",
    ".com",
    ".lnk",
}


@dataclass(slots=True)
class TexturePackAnalysis:
    counts: Counter[str] = field(default_factory=Counter)
    unknown_extensions: Counter[str] = field(default_factory=Counter)
    executable_files: list[str] = field(default_factory=list)
    total_files: int = 0

    @property
    def unknown_count(self) -> int:
        return sum(self.unknown_extensions.values())


class TexturePackAnalyzer:
    def analyze_folder(self, folder: Path) -> TexturePackAnalysis:
        analysis = TexturePackAnalysis()
        for path in folder.rglob("*"):
            if path.is_file():
                relative_name = str(path.relative_to(folder))
                self._inspect_path(path.name, relative_name, analysis)
        return analysis

    def analyze_zip(self, archive: Path) -> TexturePackAnalysis:
        analysis = TexturePackAnalysis()
        with ZipFile(archive) as zip_file:
            for item in zip_file.infolist():
                if item.is_dir():
                    continue
                name = PurePosixPath(item.filename).name
                self._inspect_path(name, item.filename, analysis)
        return analysis

    @staticmethod
    def _inspect_path(
        file_name: str,
        display_name: str,
        analysis: TexturePackAnalysis,
    ) -> None:
        extension = Path(file_name).suffix.lower()
        analysis.total_files += 1

        if extension in TEXTURE_PACK_EXTENSIONS:
            analysis.counts[TEXTURE_PACK_EXTENSIONS[extension]] += 1
            return

        if extension in EXECUTABLE_EXTENSIONS:
            analysis.executable_files.append(display_name)
            return

        if extension:
            analysis.unknown_extensions[extension] += 1
        else:
            analysis.unknown_extensions["No extension"] += 1


class TexturePackScannerPage:
    def __init__(
        self,
        console: Console,
        settings_store: SettingsStore,
        file_picker: FilePicker,
    ) -> None:
        self.console = console
        self.settings_store = settings_store
        self.file_picker = file_picker
        self.analyzer = TexturePackAnalyzer()
        self.selected_folder: Path | None = None
        self.selected_zip: Path | None = None
        self.source_label = "None"
        self._logger = logging.getLogger(__name__)

    def open(self) -> None:
        while True:
            self._render()
            choice = Prompt.ask(
                f"{CRT_PROMPT} SELECT",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                show_choices=False,
            )

            if choice == "1":
                self._select_folder()
            elif choice == "2":
                self._select_zip()
            elif choice == "3":
                self._scan()
            elif choice in {"4", "5", "6", "7"}:
                self._coming_soon()
            elif choice == "8":
                return

    def _render(self) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Texture Pack Scanner"))

        source_table = crt_data_table("Scanner Status", show_header=False)
        source_table.add_column("Name", style=f"bold {CRT_GREEN}", no_wrap=True)
        source_table.add_column("Value", style=CRT_MUTED)
        source_table.add_row("Selected Folder", str(self.selected_folder or "Not selected"))
        source_table.add_row("Selected ZIP", str(self.selected_zip or "Not selected"))
        source_table.add_row("Current Source", self.source_label)
        self.console.print(source_table)
        self.console.print()
        self.console.print(
            crt_menu(
                "Actions",
                (
                    ("1", "Select Folder"),
                    ("2", "Select ZIP Archive"),
                    ("3", "Scan"),
                    ("4", "Hash Generator"),
                    ("5", "Export Report"),
                    ("6", "Deep Scan"),
                    ("7", "Extension Statistics"),
                    ("8", "Back"),
                ),
            )
        )
        self.console.print(crt_footer("Minecraft", "PRESS 8 TO GO BACK"))
        self.console.print()

    def _select_folder(self) -> None:
        self._clear_if_enabled()
        self.console.print(crt_message("Folder Picker", "Opening native folder picker..."))
        try:
            selected = self.file_picker.select_folder()
        except Exception as exc:
            self._logger.exception("Folder selection failed.")
            self._message("Folder Selection Failed", str(exc), CRT_DANGER)
            return

        if selected is None:
            self._message("Folder Selection", "No folder was selected.", CRT_WARNING)
            return

        self.selected_folder = selected
        self.selected_zip = None
        self.source_label = "Folder"
        self._message("Folder Selected", str(selected), CRT_GREEN)

    def _select_zip(self) -> None:
        self._clear_if_enabled()
        self.console.print(crt_message("File Picker", "Opening native file picker..."))
        try:
            selected = self.file_picker.select_file(
                title="Select ZIP Archive",
                filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")],
            )
        except Exception as exc:
            self._logger.exception("ZIP selection failed.")
            self._message("ZIP Selection Failed", str(exc), CRT_DANGER)
            return

        if selected is None:
            self._message("ZIP Selection", "No ZIP archive was selected.", CRT_WARNING)
            return

        self.selected_zip = selected
        self.selected_folder = None
        self.source_label = "ZIP Archive"
        self._message("ZIP Archive Selected", str(selected), CRT_GREEN)

    def _scan(self) -> None:
        try:
            if self.selected_folder is not None:
                analysis = self.analyzer.analyze_folder(self.selected_folder)
                source = str(self.selected_folder)
            elif self.selected_zip is not None:
                analysis = self.analyzer.analyze_zip(self.selected_zip)
                source = str(self.selected_zip)
            else:
                self._message("Scan", "Select a folder or ZIP archive first.", CRT_WARNING)
                return
        except BadZipFile:
            self._logger.exception("Invalid ZIP archive.")
            self._message(
                "Scan Failed",
                "The selected file is not a valid ZIP archive.",
                CRT_DANGER,
            )
            return
        except OSError as exc:
            self._logger.exception("Texture pack scan failed.")
            self._message("Scan Failed", str(exc), CRT_DANGER)
            return

        self._render_report(source, analysis)

    def _render_report(self, source: str, analysis: TexturePackAnalysis) -> None:
        self._clear_if_enabled()
        self.console.print()
        self.console.print(crt_header("Texture Pack Analysis"))
        self.console.print(f"[bold {CRT_GREEN}]SOURCE:[/bold {CRT_GREEN}] [{CRT_MUTED}]{source}[/{CRT_MUTED}]")
        self.console.print()

        counts = crt_data_table("File Counts", show_header=False)
        counts.add_column("Type", style=f"bold {CRT_GREEN}", no_wrap=True)
        counts.add_column("Count", justify="right", style=CRT_MUTED)
        for label in ["PNG", "JSON", "OGG", "MCMETA", "Properties", "Text files"]:
            counts.add_row(label, str(analysis.counts[label]))
        counts.add_row("Unknown", str(analysis.unknown_count))
        counts.add_row("Total files", str(analysis.total_files))
        self.console.print(counts)
        self.console.print()

        executable_table = Table(
            title="Executable Files",
            box=box.SQUARE,
            border_style=CRT_DANGER if analysis.executable_files else CRT_GREEN,
            show_lines=False,
        )
        executable_table.add_column("Path", style=CRT_MUTED)
        if analysis.executable_files:
            for path in analysis.executable_files:
                executable_table.add_row(path)
        else:
            executable_table.add_row("None")
        self.console.print(executable_table)
        self.console.print()

        status = (
            "Executable or script file types were detected."
            if analysis.executable_files
            else "No suspicious executable file types were found."
        )
        style = CRT_DANGER if analysis.executable_files else CRT_GREEN
        self.console.print(crt_message("Status", status, style))
        self.console.print()

        if not analysis.executable_files:
            self.console.print(f"[{CRT_GREEN}]No executable files detected.[/{CRT_GREEN}]")
            self.console.print()

        self.console.print(crt_footer("Minecraft", "PRESS ENTER TO GO BACK"))
        self._wait_for_back()

    def _coming_soon(self) -> None:
        self._message("Coming Soon", "Coming Soon", CRT_WARNING)

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
