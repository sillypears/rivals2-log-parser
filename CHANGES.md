# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 2025-11-13: Modified tab order in `main.py` to make only the name entry box and opponent ELO spinbox tabbable, excluding all other widgets from tab navigation.
- 2025-11-13: Improved network error handling across the application, adding specific exception handling for timeouts, connection errors, and general request failures, with user-friendly notifications in the GUI.
- 2025-11-13: Added closeEvent method in `MainWindow` to properly stop background parser threads when closing the application window.
- 2025-11-13: Added signal handling for SIGINT to allow graceful termination via Ctrl+C from the console.
- 2025-11-13: Fixed dropdown separators to display horizontal lines instead of "sepior" text in PySide6.
- 2025-11-13: Updated icon loading to use RGB PNG format and proper path handling for both source and compiled binaries on Linux for PySide6 compatibility.