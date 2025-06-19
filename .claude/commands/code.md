# Claude Coding Agent Instructions for Pasta Development

## Project Overview

You are tasked with developing **Pasta**, a cross-platform system tray application that converts clipboard content into simulated keyboard input. This project follows Test-Driven Development (TDD) principles, uses UV package management, and maintains high code quality standards.

## Critical Requirements

1. **Follow the PRD**: Work through the `pasta-prd.md` document systematically, checking off each task as you complete it
2. **TDD Approach**: ALWAYS write tests before implementation
3. **Code Quality**: Run linting and formatting after each file creation/modification
4. **Documentation**: Add docstrings to all classes and functions
5. **Type Hints**: Use type hints for all function parameters and returns
6. **Line Length**: Maximum 140 characters per line

## Development Workflow

For each task in the PRD:

1. **Read** the task carefully
2. **Write tests** first (if it's a test task)
3. **Implement** the feature (if it's an implementation task)
4. **Lint** the code: `uv run ruff check . --fix && uv run ruff format .`
5. **Test** the implementation: `uv run pytest -xvs`
6. **Update** the PRD by checking off the completed task
7. **Commit** your changes with a descriptive message

## Project Structure

Maintain this exact structure:
```
pasta/
├── src/
│   └── pasta/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── clipboard.py
│       │   ├── keyboard.py
│       │   ├── storage.py
│       │   └── hotkeys.py
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── tray.py
│       │   ├── settings.py
│       │   ├── history.py
│       │   └── resources/
│       └── utils/
│           ├── __init__.py
│           ├── platform.py
│           ├── permissions.py
│           └── security.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
├── docs/
├── .github/
│   └── workflows/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── LICENSE
└── uv.lock
```

## Code Standards

### Example Test Structure
```python
"""Tests for the ClipboardManager module."""
import pytest
from unittest.mock import Mock, patch
from pasta.core.clipboard import ClipboardManager


class TestClipboardManager:
    """Test cases for ClipboardManager."""

    @pytest.fixture
    def manager(self):
        """Create a ClipboardManager instance for testing."""
        return ClipboardManager(history_size=10)

    def test_initialization(self, manager):
        """Test ClipboardManager initializes correctly."""
        assert manager.history == []
        assert manager.history_size == 10
        assert not manager.monitoring

    def test_clipboard_monitoring_starts(self, manager):
        """Test that clipboard monitoring can be started."""
        with patch('threading.Thread') as mock_thread:
            manager.start_monitoring()
            assert manager.monitoring
            mock_thread.assert_called_once()
```

### Example Implementation Structure
```python
"""Clipboard management functionality for Pasta."""
import hashlib
import threading
import time
from datetime import datetime
from typing import Callable, List, Optional

import pyperclip


class ClipboardManager:
    """Manages clipboard monitoring and history.

    This class provides clipboard monitoring functionality with history
    tracking and change detection.

    Attributes:
        history: List of clipboard entries
        history_size: Maximum number of entries to keep
        monitoring: Whether monitoring is active
    """

    def __init__(self, history_size: int = 100) -> None:
        """Initialize the ClipboardManager.

        Args:
            history_size: Maximum number of clipboard entries to store
        """
        self.history: List[dict] = []
        self.history_size = history_size
        self.monitoring = False
        self.callbacks: List[Callable] = []
        self._last_hash = ""
```

## Testing Guidelines

1. **Test File Naming**: Match implementation files (e.g., `clipboard.py` → `test_clipboard.py`)
2. **Test Organization**: Use classes to group related tests
3. **Fixtures**: Use pytest fixtures for reusable test components
4. **Mocking**: Mock external dependencies (clipboard, file system, etc.)
5. **Coverage**: Aim for >90% code coverage

## Implementation Guidelines

1. **Single Responsibility**: Each class/function should do one thing well
2. **Error Handling**: Use try/except blocks for external operations
3. **Logging**: Add appropriate logging statements
4. **Constants**: Define magic numbers and strings as class/module constants
5. **Platform Checks**: Use `platform.system()` for OS-specific code

## Phase Execution Instructions

### Phase 1: Project Setup
Start by setting up the project structure exactly as specified. Create all directories and placeholder files. Ensure UV is configured correctly with all dependencies.

### Phase 2-3: Core Modules (TDD)
For each core module:
1. Write comprehensive tests covering all functionality
2. Run tests (they should fail)
3. Implement the module to make tests pass
4. Refactor for clarity and performance

### Phase 4-5: System Tray
Focus on creating a clean, minimal UI that works consistently across platforms. The tray icon should be simple and professional.

### Phase 6-7: Settings System
Keep the settings UI minimal. Only essential options should be exposed to users.

### Phase 8-9: Advanced Features
These are enhancement features. Ensure core functionality is solid before implementing.

### Phase 10: Integration
This is where everything comes together. Focus on smooth interactions between components.

### Phase 11: Platform-Specific
Handle platform differences gracefully with clear fallbacks.

### Phase 12-13: Polish
Documentation and packaging are crucial for a professional product.

## Common Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -xvs                    # Stop on first failure, verbose
uv run pytest --cov=pasta            # With coverage
uv run pytest -k "test_clipboard"    # Run specific tests

# Code quality
uv run ruff check . --fix           # Lint and auto-fix
uv run ruff format .                # Format code
uv run mypy src/                    # Type checking

# Run the application
uv run python -m pasta

# Build
uv build
```

## Important Reminders

1. **Check off tasks** in the PRD as you complete them
2. **Test first**, implement second
3. **Keep commits small** and focused
4. **Run linting** after every change
5. **Document** as you go
6. **Ask for clarification** if requirements are unclear

## Error Handling Strategy

1. **User-Facing Errors**: Show friendly messages, log details
2. **System Errors**: Fail gracefully, maintain application stability
3. **Permission Errors**: Guide users to fix permissions
4. **Resource Errors**: Implement retry logic where appropriate

## Security Considerations

1. **Never log** sensitive clipboard content
2. **Encrypt** sensitive data at rest
3. **Rate limit** all operations
4. **Validate** all inputs
5. **Clean up** resources on exit

## Final Checklist Before Moving to Next Task

- [ ] Tests written and passing
- [ ] Code linted and formatted
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] No hardcoded values
- [ ] Error handling in place
- [ ] Task checked off in PRD
- [ ] Changes committed

---

## Start Development

Begin with Phase 1, Task 1: Install UV package manager. Work through each task systematically, maintaining high quality throughout. Remember: this is a professional application that users will rely on daily. Make it robust, fast, and delightful to use.

Good luck! 🚀
