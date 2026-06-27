# Contributing

Thank you for your interest in contributing to BAUM TOOLS V1.

## Development Setup

1. Install Python 3.13 or newer.
2. Clone the repository.
3. Run `start.bat`.

The launcher creates a virtual environment and installs dependencies automatically.

## Project Guidelines

- Keep user-facing text in English.
- Keep tools modular and category-specific.
- Do not place feature logic directly in `ui.py` unless it belongs to global navigation.
- Use type hints for new code.
- Keep comments minimal and useful.
- Avoid claims that scanned files are safe or malicious.
- Add new third-party dependencies through imports and keep `requirements.txt` updated.

## Adding Tools

New categories should live under `modules/`.

Example:

```text
modules/
  category_name/
    category_menu.py
    tool_name.py
```

## Pull Requests

Before opening a pull request:

- Run the application through `start.bat`.
- Check that the terminal UI remains clean and readable.
- Verify that new modules do not break existing navigation.
- Update `README.md` and `CHANGELOG.md` when user-facing behavior changes.
