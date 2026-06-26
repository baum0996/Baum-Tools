# BAUM TOOLS V1

BAUM TOOLS V1 is a modern Windows terminal-based multi-tool application for inspection, analysis, and utility workflows.

It is designed to help users inspect folders, ZIP archives, Minecraft texture packs, Windows startup entries, and basic system information in a clean and organized way. The project is built with a modular structure so more categories and tools can be added over time.

Developed by baum and ChatGPT.

## Important Disclaimer

BAUM TOOLS V1 is **not an antivirus**.

It does **not** claim that files are safe, virus-free, infected, malicious, or clean.

The application only reports information, file characteristics, and potentially unusual indicators so users can review them. It does not replace antivirus software, Windows Defender, VirusTotal, or professional malware analysis tools.

Always be careful when opening files from unknown sources.

## AI-Assisted Project

This project was created by baum with assistance from ChatGPT.

AI was used to help design the structure, write code, improve documentation, and plan future features. The project is intended to grow over time as an open-source tool.

## Features

- Modern terminal interface using Rich
- Windows CMD / Windows Terminal support
- Category-based tool navigation
- Native Windows folder picker
- Native Windows file picker
- Automatic dependency installation through `start.bat`
- Automatic virtual environment setup
- Persistent JSON settings
- Logging support
- Modular project structure
- GitHub-ready open-source layout

## Current Tool Categories

### Minecraft

#### Texture Pack Scanner

The Texture Pack Scanner can analyze a Minecraft texture pack folder or ZIP archive.

It displays:

- PNG file count
- JSON file count
- OGG audio file count
- MCMETA file count
- Properties file count
- Text file count
- Unknown extension count
- Total file count

It can also detect executable or script-like file types, including:

- EXE
- DLL
- BAT
- CMD
- PS1
- VBS
- JS
- JAR
- MSI
- SCR
- COM
- LNK

If these file types are found, the tool lists them clearly for review.

It does **not** delete, disable, quarantine, block, or open any files.

### Windows

#### Startup Analyzer

The Startup Analyzer performs read-only inspection of Windows startup locations.

It checks:

- Registry startup entries
- Startup folders
- Startup/logon-related scheduled tasks

It displays:

- Entry name
- File path
- Source
- Publisher, if available
- Basic heuristic indicator, if applicable

If something looks unusual, it may be labeled only as:

```text
Unusual entry (heuristic indicator)
This is not a malware verdict. It is only an informational indicator.
The Startup Analyzer does not modify, disable, remove, execute, or clean any startup item.
System Info Dashboard
The System Info Dashboard displays read-only system information.
It shows:
Windows version
Build number
Architecture
CPU model
CPU cores and threads
Total RAM
Available RAM
Drive list
Free space and total space per drive
Python version
Virtual environment status
Hostname
Local IP address, if available
Timestamp of collected information
It does not optimize, clean, modify, or change system settings.
Screenshots
Screenshots will be added in a future release.
Installation
Install Python 3.13 or newer from:
https://www.python.org/downloads/
During installation, enable:
Add python.exe to PATH
No manual dependency installation is required.
Usage
Download or clone the project, then double-click:
start.bat
The launcher will automatically:
Check for Python 3.13+
Create a .venv virtual environment if needed
Activate the virtual environment
Upgrade pip
Install dependencies from requirements.txt
Start BAUM TOOLS V1
No command line knowledge is required.
Requirements
Windows
Python 3.13+
CMD or Windows Terminal
Python dependencies are listed in:
requirements.txt
Current dependencies:
colorama>=0.4.6
psutil>=6.1.0
rich>=13.9.0
Project Structure
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
  windows/
    windows_menu.py
    startup_analyzer/
      startup_analyzer.py
      startup_menu.py
    system_info/
      system_info.py
      system_menu.py
tools/
  sync_requirements.py
assets/
logs/
requirements.txt
start.bat
README.md
LICENSE
CHANGELOG.md
CONTRIBUTING.md
pyproject.toml
settings.json
Roadmap
Planned future features include:
Hash Generator
Export Report
Deep Scan
Extension Statistics
More Minecraft tools
More Windows tools
Network tools
File tools
Utility tools
Plugin system
Recent folders
Improved reporting
Optional export formats
Open Source
BAUM TOOLS V1 is intended to be an open-source GitHub project.
Contributions should keep the project:
modular
readable
terminal-based
Windows-friendly
read-only where system inspection is involved
honest about what the tool can and cannot detect
License
This project is licensed under the MIT License.
