from __future__ import annotations

import sys

from colorama import just_fix_windows_console

from logger import configure_logging
from settings import SettingsStore
from ui import BaumToolsApp


def main() -> None:
    if sys.version_info < (3, 12):
        print("Python 3.12 or newer is required.")
        print("Install Python 3.12 or newer, then start BAUM TOOLS again.")
        raise SystemExit(1)

    just_fix_windows_console()
    configure_logging()

    settings_store = SettingsStore()
    app = BaumToolsApp(settings_store)
    app.run()


if __name__ == "__main__":
    main()
