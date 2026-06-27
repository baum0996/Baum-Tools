from __future__ import annotations

from pathlib import Path


APP_NAME = "BAUM TOOLS V1"
APP_SUBTITLE = "Multi Data Analyzing Tool"
APP_VERSION = "1.0.0"
APP_DEVELOPER = "baum and ChatGPT"
APP_DESCRIPTION = (
    "A terminal-based inspection and analysis tool for folders, ZIP archives, "
    "and individual files."
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"
SETTINGS_PATH = BASE_DIR / "settings.json"
LOG_PATH = LOGS_DIR / "baum_tools.log"

MENU_OPTIONS = {
    "1": "Minecraft",
    "2": "Windows",
    "3": "Discord",
    "4": "Network",
    "5": "File Tools",
    "6": "Utilities",
    "7": "Settings",
    "8": "About",
    "9": "Exit",
}

THEMES = ["Default", "High Contrast", "Calm"]

FUTURE_FEATURES = [
    "Folder Scanner",
    "ZIP Scanner",
    "Single File Scanner",
    "SHA-256 Generator",
    "MD5 Generator",
    "VirusTotal Integration",
    "YARA Rule Support",
    "Entropy Analysis",
    "Digital Signature Verification",
    "File Extension Statistics",
    "Duplicate File Detection",
    "Report Export (TXT / JSON)",
    "Plugin System",
    "Recent Folders",
    "Drag & Drop",
    "Deep Scan",
    "Quick Scan",
]
