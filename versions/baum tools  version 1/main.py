from __future__ import annotations

from colorama import just_fix_windows_console

from logger import configure_logging
from settings import SettingsStore
from ui import BaumToolsApp


def main() -> None:
    just_fix_windows_console()
    configure_logging()

    settings_store = SettingsStore()
    app = BaumToolsApp(settings_store)
    app.run()


if __name__ == "__main__":
    main()
