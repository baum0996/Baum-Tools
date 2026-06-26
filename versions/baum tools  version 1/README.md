# BAUM TOOLS V1

BAUM TOOLS V1 is a modern Windows terminal toolbox for inspection, analysis, and utility workflows.

The project is designed as a modular multi-tool platform. Categories and tools can be added without turning the main application into one large file. The current implemented category is Minecraft, including a Texture Pack Scanner for folders and ZIP archives.

Developed by baum and ChatGPT.

## Features

- Clean Rich-powered terminal interface
- Category-based navigation
- Native Windows folder and file pickers
- Persistent JSON settings
- Logging support
- Automatic virtual environment setup through `start.bat`
- Automatic dependency installation from `requirements.txt`
- Minecraft Texture Pack Scanner
- Folder and ZIP archive analysis
- Counts PNG, JSON, OGG, MCMETA, properties, text, and unknown file extensions
- Detects executable and script-like file types without making safety claims
- Modular structure ready for future categories and tools

## Screenshots

Screenshots will be added in a future release.

## Installation

Install Python 3.13 or newer from:

```text
https://www.python.org/downloads/
```

During installation, enable:

```text
Add python.exe to PATH
```

No manual dependency installation is required.

## Usage

Double-click:

```text
start.bat
```

The launcher will:

- Check for Python 3.13+
- Create `.venv` if needed
- Activate the virtual environment
- Upgrade pip
- Synchronize `requirements.txt` with detected third-party imports
- Install dependencies
- Start BAUM TOOLS V1

Advanced users can also run:

```cmd
start.bat
```

## Project Structure

```text
main.py
ui.py
constants.py
settings.py
models.py
filepicker.py
logger.py
utils.py
scanner.py
zipscanner.py
hashing.py
modules/
  minecraft/
    minecraft_menu.py
    texture_pack_scanner.py
tools/
  sync_requirements.py
assets/
logs/
requirements.txt
start.bat
```

## Roadmap

- Windows tools
- Network tools
- File tools
- General utilities
- Hash generator
- Exportable reports
- Deep scan mode
- Extension statistics
- Plugin support
- Recent folders
- Additional Minecraft analysis tools

## Disclaimer

BAUM TOOLS V1 is an inspection and analysis tool, not an antivirus. It does not claim that files are safe or malicious. It reports file characteristics and potentially suspicious executable file types so users can review them.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
