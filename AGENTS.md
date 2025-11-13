# AGENTS.md

This file contains notes, commands, and configurations for the opencode agent to reference during development.

## Project Overview
- **Name**: rivals2-log-parser
- **Purpose**: Parse Rivals 2 game logs to track ELO changes and match data via a GUI application.
- **Tech Stack**: Python, PySide6 (Qt), MySQL/MariaDB, Requests for API calls.

## Recent Changes
- **GUI Modernization**: Replaced Tkinter with PySide6 for a modern, cross-platform GUI.
  - Removed borders and frames for cleaner layout.
  - Used QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout.
  - Implemented QThread for background parsing with signals/slots.
  - Added QCompleter for autocomplete in name field.
- **Dependencies**: Added PySide6==6.8.1 to requirements.txt and pyproject.toml dev dependencies.
- **Build**: PyInstaller commands updated for PySide6 bundling.
- **Tab Order Adjustment**: Modified tab navigation in main.py to only allow tabbing between the name entry box and opponent ELO spinbox, excluding all other widgets from tab order.
- **Network Error Handling**: Improved error handling for all network requests in main.py and log_parser.py, adding specific exception catching (Timeout, ConnectionError, RequestException), timeouts, and user notifications for failures.
- **Application Shutdown Fix**: Added proper closeEvent handling to stop background threads and signal handling for Ctrl+C to ensure clean application shutdown.
- **Dropdown Separators**: Fixed dropdown separators in PySide6 by inserting horizontal lines for "sepior" items instead of displaying them as text.
- **Icon Loading**: Updated icon handling to use an RGB-converted PNG for Linux, with proper path resolution for both source and compiled binaries to ensure compatibility with PySide6/Qt.

## Key Files
- `main.py`: Main GUI application (PySide6).
- `log_parser.py`: Log parsing logic.
- `db/database.py`: Database interface.
- `utils/calc_elo.py`: ELO calculation.
- `requirements.txt`: Python dependencies.
- `pyproject.toml`: Project configuration.

## Commands
- **Run Application**: `python main.py`
- **Build EXE (Windows)**: `pyinstaller --onefile --windowed --icon=icon.ico --add-data "config.ini;." --add-data "icon.png;." main.py`
- **Build Binary (Linux)**: `python build_linux.py build`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Test Database**: `python tests/test_db.py`

## Linting/Type Checking
- No specific linting command found yet. Suggest running `ruff` or `mypy` if available.

## Notes for Agent
- Use PySide6 for any GUI-related tasks.
- For threading, use QThread with signals to update UI safely.
- Database uses MariaDB/MySQL; ensure credentials are in environment variables.
- Log parsing targets Rivals 2 game logs in platform-specific directories.