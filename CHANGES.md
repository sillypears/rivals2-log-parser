# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 2025-11-16: Added "Paste JSON" button to import match data from clipboard back into the UI fields.
- 2025-11-17: Added right-click reset functionality for all input widgets (spinboxes, combos, line edits, checkboxes) to restore them to initial values.

### Changed
- 2025-11-13: Modified tab order in `main.py` to make only the name entry box and opponent ELO spinbox tabbable, excluding all other widgets from tab navigation.
- 2025-11-13: Improved network error handling across the application, adding specific exception handling for timeouts, connection errors, and general request failures, with user-friendly notifications in the GUI.
- 2025-11-13: Added closeEvent method in `MainWindow` to properly stop background parser threads when closing the application window.
- 2025-11-13: Added signal handling for SIGINT to allow graceful termination via Ctrl+C from the console.
- 2025-11-13: Fixed dropdown separators to display horizontal lines instead of "sepior" text in PySide6.
- 2025-11-13: Updated icon loading to use RGB PNG format and proper path handling for both source and compiled binaries on Linux for PySide6 compatibility.
- 2025-11-16: Fixed log directory path to be absolute to prevent logs from being created in temp directories for executables.
- 2025-11-16: Updated log file opening to use subprocess with modified environment to avoid Qt library conflicts in built binaries.
- 2025-11-16: Removed Tkinter references from build script as the app now uses PySide6.
- 2025-11-16: Corrected final_move_id submission in parser to use the final move from the last played game.
- 2025-11-16: Enhanced logging in parser to include final_move_id in insertion messages.
- 2025-11-16: Removed "final_move_id" from generated JSON as it's not needed.
- 2025-11-17: Fixed QAction import from PySide6.QtWidgets to PySide6.QtGui for PySide6 compatibility.
- 2025-11-17: Optimized window sizing to be as compact as possible by reducing combo box minimum widths to 80px and using adjustSize() for dynamic minimal sizing.
- 2025-11-17: Reduced name entry field minimum width to 30px for tighter layout.
- 2025-11-18: Rearranged GUI layout to be more vertical: moved buttons above ELO inputs, positioned name input above game sections spanning multiple columns.
- 2025-11-18: Fixed index error in durations button when filling in match times for matches with fewer than 3 games.

### Fixed
- 2025-12-12: Fixed final move ID lookup for moves containing "*" in their names by removing unnecessary string replacement in moves.get() calls.
- 2025-12-12: Updated validation logic to not require final move selection when winner checkbox is checked (indicating opponent won the game).