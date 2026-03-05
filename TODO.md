# TODO.md - Rivals2 Log Parser Improvements

This file contains expanded suggestions for improving the Rivals2 Log Parser project, based on a codebase analysis. Each suggestion includes detailed rationale, specific actions, and implementation guidance.

## 1. Improve Documentation

### Rationale
The current README.md is inadequate, with a placeholder title and minimal content that doesn't provide essential information for users or contributors. Lack of documentation hinders adoption, makes setup confusing, and prevents effective collaboration. Key modules like log_parser.py and utils/calc_elo.py lack inline documentation.

### Detailed Actions
- **Rewrite README.md comprehensively**:
  - Add a professional project title and description: "Rivals2 Log Parser: A GUI application for parsing Rivals of Aether 2 game logs, tracking ELO changes, and managing match data."
  - Include sections: Overview, Features, Installation, Configuration, Usage, Screenshots, Contributing, License, Troubleshooting.
  - Provide step-by-step installation instructions, including Python version requirements (e.g., Python 3.8+), virtual environment setup, and dependency installation.
  - Document configuration: Explain config.ini structure, required fields (e.g., API keys), and how to use config_template.ini.
  - Add usage examples: Screenshots of the GUI, command-line options if added, sample log parsing workflow.
- **Add API documentation**:
  - Use docstrings in all Python files following PEP 257 (e.g., in main.py for GUI methods, log_parser.py for parsing functions).
  - Generate HTML docs using Sphinx: Create docs/ directory, add conf.py, and document key classes/functions like `parse_log()` in log_parser.py or `calculate_elo()` in utils/calc_elo.py.
  - Include examples: Code snippets showing how to use the parser programmatically.
- **Additional docs**: Create CHANGELOG.md summarizing recent changes (from AGENTS.md), and CONTRIBUTING.md with coding standards and PR guidelines.

### Impact and Priority
High priority for user adoption and maintenance. Without clear docs, new contributors struggle, and users can't effectively use the tool.

---

## 2. Strengthen Testing

### Rationale
The codebase has minimal testing, leaving critical functionality untested. This risks bugs in log parsing, ELO calculations, API interactions, and GUI elements, especially after changes.

### Detailed Actions
- **Add unit tests**:
  - Use pytest for testing. Create tests/ directory with files like test_parser.py, test_elo.py, test_gui.py.
  - Test log_parser.py: Mock file reading and test regex parsing for various log formats (e.g., different game outcomes, moves with "*").
  - Test utils/calc_elo.py: Verify ELO calculations with edge cases (e.g., new players, draws, high/low ratings).
  - Test main.py: Use QtTest or pytest-qt for GUI elements like button clicks, form validation, and thread safety.
- **Add integration tests**:
  - Test full workflows: Parsing a sample log file and submitting data via API.
  - Mock external dependencies: Use pytest-mock for network requests (e.g., API calls in log_parser.py).
- **Set up CI/CD**:
  - Create .github/workflows/ci.yml for GitHub Actions: Run tests on pushes/PRs, using Python versions 3.8-3.11.
  - Add coverage: Use pytest-cov or coverage.py to measure test coverage, aim for >80%.
  - Include linting: Run ruff or flake8 in CI.
- **Test infrastructure**: Add sample test data (e.g., test_logs/ directory with anonymized log files).

### Impact and Priority
Critical for reliability. Untested code leads to regressions; comprehensive tests ensure stability during refactoring (e.g., GUI modernization).

---

## 3. Add Type Hints and Code Quality

### Rationale
Type hints are missing in most files, leading to runtime errors and poor IDE support. No automated code quality checks mean style inconsistencies and potential bugs persist.

### Detailed Actions
- **Add type hints**:
  - Update main.py: Add hints for GUI methods, e.g., `def update_ui(self, data: dict[str, Any]) -> None:`.
  - Update log_parser.py: Hint parsing functions, e.g., `def parse_log(file_path: str) -> list[dict[str, Any]]:`.
  - Use typing module: Import `from typing import List, Dict, Optional, Any`.
- **Configure code quality tools**:
  - Install ruff: Add to requirements-dev.txt or pyproject.toml. Configure in pyproject.toml for linting, formatting, and type checking.
  - Set up pre-commit hooks: Use pre-commit framework, add .pre-commit-config.yaml with ruff, mypy, and black.
  - Run tools: `ruff check .` for linting, `mypy .` for type checking. Fix issues like unused imports or style violations.
- **Refactor code**: Extract hardcoded values (e.g., theme colors in main.py) into constants or config files. Ensure consistent naming (e.g., snake_case for functions).

### Impact and Priority
Improves maintainability and catches errors early. Type hints reduce bugs in complex logic like ELO calculations.

---

## 4. Enhance Security and Error Handling

### Rationale
Bare `except` clauses mask errors, and poor logging exposes sensitive data. Unvalidated inputs and network calls pose security risks, especially with user-provided logs or API keys.

### Detailed Actions
- **Improve error handling**:
  - Replace bare `except` in log_parser.py (lines 91, 105) with specific exceptions: `except FileNotFoundError:` for missing files, `except ValueError:` for invalid data.
  - Add custom exceptions: Define in utils/errors.py for parsing errors or API failures.
- **Enhance security**:
  - Validate inputs: In main.py, check ELO inputs (e.g., positive integers), sanitize log file paths.
  - Secure logging: Replace `print()` with `logging` module (import logging). Set up log levels, and ensure sensitive data (e.g., API keys) isn't logged.
  - Network security: Add timeouts and retries for requests in log_parser.py. Validate API responses.
  - Config security: Ensure config.ini is gitignored; use environment variables for secrets.
- **Logging setup**: Configure logging in main.py or a separate utils/logger.py, with file output and rotation.

### Impact and Priority
Reduces vulnerabilities and improves debugging. Poor handling can cause crashes or data exposure.

---

## 5. Fix Dependencies and Inconsistencies

### Rationale
Missing dependencies cause import errors, platform restrictions limit usability, and inconsistencies confuse setup. No CLI mode restricts automation.

### Detailed Actions
- **Update dependencies**:
  - Ensure all imports are covered: Check pyproject.toml dev dependencies for PySide6 and requests for API calls.
- **Enable cross-platform support**:
  - Remove MacOS block in log_parser.py (line 25): Add platform-specific path handling using `platform.system()` and config options.
- **Add CLI mode**:
  - Modify main.py: Use argparse to add CLI arguments (e.g., --input-log, --submit-api).
  - Implement headless parsing: Skip GUI if CLI args provided, output results to console or file.
- **Config improvements**: Add config_template.ini to repo (renamed from config_template.ini), with example values (e.g., placeholder API keys).

### Impact and Priority
Essential for usability. Fixes ensure the app runs everywhere and supports scripted use cases.