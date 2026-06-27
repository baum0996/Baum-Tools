from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AppSettings:
    theme: str = "Default"
    animations: bool = True
    auto_clear_console: bool = True
    scan_hidden_files: bool = False
    show_file_sizes: bool = True
    confirm_before_exit: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AppSettings":
        defaults = cls()
        return cls(
            theme=str(data.get("theme", defaults.theme)),
            animations=bool(data.get("animations", defaults.animations)),
            auto_clear_console=bool(
                data.get("auto_clear_console", defaults.auto_clear_console)
            ),
            scan_hidden_files=bool(
                data.get("scan_hidden_files", defaults.scan_hidden_files)
            ),
            show_file_sizes=bool(data.get("show_file_sizes", defaults.show_file_sizes)),
            confirm_before_exit=bool(
                data.get("confirm_before_exit", defaults.confirm_before_exit)
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "theme": self.theme,
            "animations": self.animations,
            "auto_clear_console": self.auto_clear_console,
            "scan_hidden_files": self.scan_hidden_files,
            "show_file_sizes": self.show_file_sizes,
            "confirm_before_exit": self.confirm_before_exit,
        }
