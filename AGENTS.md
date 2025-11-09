# AGENTS.md

## Build Commands
- Build executable: `taskipy build` or `python build.py`
- Clean build artifacts: `taskipy clean` or `python build.py clean`
- Linux build: `python build_linux.py`

## Test Commands
- No test framework configured

## Code Style Guidelines

### Imports
- Group imports: standard library, third-party, local modules
- Use absolute imports for local modules
- Example: `from config import Config`

### Naming Conventions
- Functions/methods: snake_case (e.g., `get_current_elo`)
- Classes: PascalCase (e.g., `Config`, `Match`)
- Variables: snake_case (e.g., `opp_elo`, `match_date`)
- Constants: UPPER_CASE (e.g., `RIVALS_FOLDER`)

### Types
- Use type hints for function parameters and return values
- Use `Optional` for nullable types
- Use pydantic dataclasses for data models

### Error Handling
- Use try/except blocks with specific exception types
- Log errors with appropriate log levels
- Use `raise_for_status()` for HTTP requests

### Formatting
- Use f-strings for string interpolation
- Use 4-space indentation
- Line length: no strict limit but keep readable
- Use blank lines to separate logical sections

### Logging
- Use the logging module with appropriate levels (DEBUG, INFO, ERROR)
- Include timestamps and module names in log format
- Use rotating file handlers for log persistence</content>
<parameter name="filePath">/home/blap/projects/rivals2-log-parser/AGENTS.md