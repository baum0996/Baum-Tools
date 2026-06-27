from __future__ import annotations

import json
import logging

from constants import SETTINGS_PATH
from models import AppSettings


class SettingsStore:
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._settings = self._load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def toggle(self, key: str) -> None:
        if not hasattr(self._settings, key):
            raise KeyError(f"Unknown setting: {key}")

        value = getattr(self._settings, key)
        if not isinstance(value, bool):
            raise TypeError(f"Setting is not toggleable: {key}")

        setattr(self._settings, key, not value)
        self.save()

    def set_theme(self, theme: str) -> None:
        self._settings.theme = theme
        self.save()

    def save(self) -> None:
        SETTINGS_PATH.write_text(
            json.dumps(self._settings.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _load(self) -> AppSettings:
        if not SETTINGS_PATH.exists():
            settings = AppSettings()
            SETTINGS_PATH.write_text(
                json.dumps(settings.to_dict(), indent=2),
                encoding="utf-8",
            )
            return settings

        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Settings file must contain a JSON object.")
            return AppSettings.from_dict(raw)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self._logger.exception("Failed to load settings.")
            backup_path = SETTINGS_PATH.with_suffix(".invalid.json")
            try:
                SETTINGS_PATH.replace(backup_path)
            except OSError:
                self._logger.exception("Failed to preserve invalid settings file.")

            settings = AppSettings()
            SETTINGS_PATH.write_text(
                json.dumps(settings.to_dict(), indent=2),
                encoding="utf-8",
            )
            raise RuntimeError(
                f"Settings were reset because the settings file was invalid: {exc}"
            ) from exc
