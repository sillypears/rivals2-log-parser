# Repository Analysis: rivals2-log-parser

## Overview
This repository contains a Python application for parsing log files from the game "Rivals 2" (a fighting game). It extracts match data, calculates ELO changes, and integrates with a backend system to store and analyze match statistics. The project includes a modern GUI built with PySide6 (Qt) for user interaction.

## Project Structure
- **Root Files**:
  - `main.py`: Main GUI application entry point
  - `log_parser.py`: Core log parsing logic
  - `pyproject.toml`: Project configuration and dependencies
  - `requirements.txt`: Python package dependencies
  - `README.md`: Project documentation
  - `config.py`, `config_template.ini`: Configuration management
  - `build.py`, `build_linux.py`: Build scripts for different platforms
  - `icon.ico`, `icon.png`: Application icons

- **db/**: Database interface
  - `database.py`: MariaDB/MySQL connector for checking match existence

- **images/**: Game assets
  - `chars/`: Character portrait images (PNG files for various fighters)
  - `docs/`: Documentation images

- **queries/**: SQL queries
  - Various SQL files for data retrieval and analysis

- **tests/**: Test suite
  - `test_db.py`: Database connection tests

- **utils/**: Utility modules
  - `calc_elo.py`: ELO calculation and opponent estimation
  - `folders.py`: File system utilities
  - `match.py`: Match data model

## Key Functionality

### Log Parsing (`log_parser.py`)
- Parses Rivals 2 log files located in platform-specific directories
- Extracts rank update messages containing ELO changes
- Creates `Match` objects with detailed game information
- Posts match data to a backend API
- Handles both automatic parsing and manual data entry

### GUI Application (`main.py`)
- PySide6-based desktop application with modern, cross-platform interface
- Fetches character, stage, and move data from backend
- Allows manual input of match details (opponent, stages, final moves)
- Displays current ELO and match history
- Provides buttons for parsing logs, viewing logs, refreshing data, copying JSON, and clearing fields
- Includes theme selector (e.g., Catppuccin, Dracula, Nord), autocomplete for opponent names, and restricted tab order (only name entry and opponent ELO spinbox)
- Uses QThread for background parsing to avoid UI freezing

### ELO Calculation (`utils/calc_elo.py`)
- Estimates opponent ELO based on your ELO change
- Implements ELO rating system with K-factors for different scenarios
- Accounts for win streaks and placement matches

### Database Integration
- Connects to MariaDB/MySQL database
- Checks for duplicate matches before insertion
- Supports seasonal data partitioning

## Dependencies
- **Core**: PySide6 (GUI), requests, pydantic, python-dotenv
- **Database**: mysql-connector-python
- **Build**: pyinstaller, setuptools, pyinstaller-hooks-contrib
- **Utilities**: pillow (for images), psutil, typing-inspection, urllib3, certifi

## Configuration
- Uses INI file for configuration (`config.ini`)
- Supports environment variables via `.env` files
- Configurable logging with rotating file handlers
- Platform-specific paths for log file locations

## Build System
- Uses PyInstaller for creating standalone executables
- Supports Windows and Linux builds
- Includes taskipy for build automation

## Testing
- Basic database connection test
- Uses pytest framework (implied by project structure)

## Architecture Notes
- **Frontend**: PySide6 (Qt) GUI for user interaction
- **Backend**: Separate service for data storage and API (referenced but not included)
- **Data Flow**: Game logs → Parser → Backend API → Database
- **Platforms**: Primarily Windows and Linux support (macOS mentioned but not fully implemented for log parsing)

## Potential Improvements
- Add more comprehensive test coverage
- Add data validation for user inputs
- Add configuration validation
- Implement proper logging levels throughout
- Add macOS support for log parsing

## Security Considerations
- Stores database credentials in environment variables
- Makes HTTP requests to backend without apparent authentication
- Handles user input that gets sent to database

## Recent Changes
- **GUI Modernization**: Replaced Tkinter with PySide6 for a modern, cross-platform GUI.
  - Removed borders and frames for cleaner layout.
  - Used QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout.
  - Implemented QThread for background parsing with signals/slots.
  - Added QCompleter for autocomplete in name field.
  - Added theme selector with multiple themes (Catppuccin Mocha/Latte, Dracula, Nord, Gruvbox Dark).
- **Dependencies**: Added PySide6==6.8.1 to requirements.txt and pyproject.toml dev dependencies.
- **Build**: PyInstaller commands updated for PySide6 bundling.
- **Tab Order Adjustment**: Modified tab navigation in main.py to only allow tabbing between the name entry box and opponent ELO spinbox, excluding all other widgets from tab order.

This project serves as a bridge between the game's log files and a centralized match tracking system, providing both automated parsing and manual data entry capabilities for Rivals 2 players.