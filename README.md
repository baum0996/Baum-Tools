# BAUM TOOLS V1

BAUM TOOLS V1 is a modern terminal-based multi-tool application for Windows.

It is designed to help users inspect folders, ZIP archives, and files in a clean and organized way. The project currently includes a Minecraft Texture Pack Scanner and is built to expand into more tools over time.

Developed by baum and ChatGPT.

## What It Does

BAUM TOOLS V1 can analyze selected folders or ZIP archives and show useful information about their contents.

The Minecraft Texture Pack Scanner can detect and count files such as:

- PNG files
- JSON files
- OGG audio files
- MCMETA files
- Properties files
- Text files
- Unknown file extensions

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

If these file types are found, the tool clearly lists them so the user can review them.

## Important Disclaimer

BAUM TOOLS V1 is **not an antivirus**.

It does **not** claim that a file is safe, virus-free, infected, or malicious.

The tool is made to inspect files and detect potentially suspicious file types or structures. It can help users notice unusual files, but it does not replace antivirus software, Windows Defender, VirusTotal, or professional malware analysis tools.

Always be careful when opening files from unknown sources.

## AI-Assisted Project

This project was created by baum with assistance from ChatGPT.

AI was used to help design the structure, write code, improve documentation, and plan future features. The project is intended to be improved over time as an open-source tool.

## Features

- Modern terminal interface
- Windows CMD support
- Native Windows folder picker
- Native Windows ZIP/file picker
- Minecraft Texture Pack Scanner
- Folder scanning
- ZIP archive scanning
- Suspicious executable file type detection
- Settings system
- Automatic dependency installation through `start.bat`
- Modular structure for future tools
- Open-source friendly project layout

## How To Use

1. Download or clone the project.
2. Make sure Python 3.13 or newer is installed.
3. Double-click `start.bat`.
4. The launcher will automatically:
   - create a virtual environment
   - install required dependencies
   - start BAUM TOOLS V1

No manual dependency installation is required.

## Requirements

- Windows
- Python 3.13 or newer
- CMD or Windows Terminal

Download Python here:

```text
https://www.python.org/downloads/
During installation, enable:
Add python.exe to PATH
Current Tools
Minecraft
Texture Pack Scanner
The Texture Pack Scanner can analyze a Minecraft texture pack folder or ZIP archive.
It displays:
file type counts
unknown extensions
executable/script-like files
a clean scan report
Roadmap
Planned future features include:
Hash Generator
Export Report
Deep Scan
Extension Statistics
Windows Tools
Network Tools
File Tools
Utilities
Plugin System
More Minecraft tools
License
This project is licensed under the MIT License.
