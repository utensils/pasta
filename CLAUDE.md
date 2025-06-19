# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pasta is a cross-platform system tray application that converts clipboard content into simulated keyboard input, bridging the gap for applications that don't support direct clipboard pasting. Built with Python using UV package management and following Test-Driven Development (TDD) principles.

## Common Development Commands

### Environment Setup
```bash
# Install UV package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project and install dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Development Workflow
```bash
# Run the application
uv run python -m pasta

# Run linting and formatting
uv run ruff check . --fix
uv run ruff format .

# Type checking
uv run mypy src/

# Run tests
uv run pytest                                    # Run all tests
uv run pytest -xvs                              # Stop on first failure, verbose
uv run pytest -v --cov=src/pasta --cov-report=term-missing       # With coverage report
uv run pytest -k "test_clipboard" -v            # Run specific tests
uv run pytest tests/unit/                       # Run unit tests only

# Build for distribution
uv build

# Create platform-specific executables
uv run pyinstaller --onefile --windowed src/pasta/__main__.py
```

## High-Level Architecture

### Core Technology Stack
- **Language**: Python 3.9+ (recommended: 3.11)
- **Package Manager**: UV (not pip)
- **System Tray**: pystray
- **Keyboard Simulation**: PyAutoGUI
- **Clipboard Access**: pyperclip
- **Testing**: pytest with pytest-qt
- **Code Quality**: Ruff (includes Black, isort, pylint functionality)
- **Line Length**: 140 characters

### Project Structure
```
pasta/
├── src/pasta/
│   ├── core/           # Core business logic
│   │   ├── clipboard.py    # ClipboardManager - monitors clipboard changes
│   │   ├── keyboard.py     # PastaKeyboardEngine - handles keyboard simulation
│   │   ├── storage.py      # SQLite-based history storage with encryption
│   │   ├── hotkeys.py      # Global hotkey registration
│   │   ├── settings.py     # Settings data model and manager
│   │   └── snippets.py     # Snippet management system
│   ├── gui/            # User interface components
│   │   ├── tray.py        # System tray implementation (pystray)
│   │   ├── settings.py    # Settings window (PyQt6)
│   │   ├── history.py     # History browser window (PyQt6)
│   │   └── resources/     # Icons and images
│   └── utils/          # Platform-specific utilities
│       ├── platform.py     # Platform detection and utilities
│       ├── permissions.py  # Permission checking and requests
│       └── security.py     # Security features (detection, rate limiting, privacy)
└── tests/
    ├── unit/           # Unit tests for individual components
    ├── integration/    # End-to-end integration tests
    └── fixtures/       # Shared test data and fixtures
```

### Key Design Patterns

1. **Multi-threaded Architecture**: Clipboard monitoring runs in a background thread to avoid blocking the UI
2. **Platform Abstraction**: Platform-specific code is isolated in utils/platform.py with unified interfaces
3. **Security First**: All sensitive clipboard data is encrypted at rest, with pattern-based detection for passwords, API keys, etc.
4. **Adaptive Performance**: Typing speed automatically adjusts based on system CPU/memory load
5. **TDD Approach**: Write tests first, then implementation - all features must have corresponding tests

### Critical Implementation Notes

1. **Permissions Handling**:
   - macOS: Requires accessibility permissions via System Preferences
   - Windows: May need UAC manifest for certain operations
   - Linux: User must be in 'input' group for device access

2. **Keyboard Simulation Methods**:
   - Use clipboard method for text >5000 chars or formatted content
   - Use typing method for smaller text to work with apps that block clipboard
   - Chunk large text into 200-char segments with adaptive delays

3. **Rate Limiting**: Implement to prevent abuse:
   - 30 pastes per 60 seconds
   - 100 clipboard reads per 60 seconds
   - 5 large pastes (>10KB) per 5 minutes

4. **Testing Considerations**:
   - Use mock fixtures for clipboard and keyboard operations
   - Set QT_QPA_PLATFORM=offscreen for headless GUI testing
   - Test on all target platforms (Ubuntu, Windows, macOS)
   - Use RLock instead of Lock for reentrant locking in SettingsManager
   - Add pytest-timeout to prevent hanging tests

### Security Requirements

- No network connections or telemetry without explicit consent
- All sensitive data encrypted using Fernet symmetric encryption
- Secure cleanup of memory on application exit
- Privacy mode to temporarily disable all monitoring
- Excluded applications list (e.g., password managers)

## TDD Development Process

When implementing features:
1. **Read** the task from pasta-prd.md
2. **Write tests** first (they should fail initially)
3. **Implement** the feature to make tests pass
4. **Lint** the code: `uv run ruff check . --fix && uv run ruff format .`
5. **Test** the implementation: `uv run pytest -xvs`
6. **Update** the PRD by checking off completed tasks
7. **Commit** changes with descriptive messages

## Code Standards

- Add comprehensive docstrings to all classes and functions
- Use type hints for all function parameters and return values
- Handle errors gracefully with appropriate try/except blocks
- Log important operations without exposing sensitive data
- Follow single responsibility principle for classes and functions
- Use `# noqa: ARG002` for unused arguments in placeholder methods during development
- Ensure all files have proper line endings (LF, not CRLF)
- No trailing whitespace or missing newlines at end of files

## Project Status

### Completed Phases
- ✅ Phase 1: Project setup and configuration
- ✅ Phase 2: Core module tests (ClipboardManager, PastaKeyboardEngine, PermissionChecker, StorageManager)
- ✅ Phase 3: Core module implementation
- ✅ Phase 4: System tray tests
- ✅ Phase 5: System tray implementation with emergency stop
- ✅ Phase 6: Settings tests and UI component tests
- ✅ Phase 7: Settings system and UI implementation
- ✅ Phase 8: Security and snippet system tests
- ✅ Phase 9: Security and snippet implementation
- ✅ CI/CD: All GitHub Actions passing on all platforms

### Current Features
- **Clipboard Monitoring**: Background thread monitors clipboard changes and saves to history
- **Clipboard History**: All copied content saved to SQLite database with encryption
- **Keyboard Engine**: Adaptive typing with chunking and platform-specific optimizations
- **Permission System**: Cross-platform permission checking and request handling
- **Storage**: SQLite-based history with encryption for sensitive data
- **System Tray**: Full menu with dynamic state updates and visual mode indicators
- **Settings**: Comprehensive settings UI with persistence and validation
- **Security**: Sensitive data detection, rate limiting, privacy mode
- **Snippets**: Full snippet management with templates and hotkeys
- **Emergency Stop**: Double ESC or tray click to abort operations
- **macOS UI/UX**: LSUIElement support, proper Cmd+W/Q handling, native window behavior
- **Paste Modes**: Auto/Clipboard/Typing modes with visual feedback (icon color changes)
  - Typing mode (orange icon) simulates keyboard input for apps that block clipboard
  - Clipboard mode (blue icon) uses standard system clipboard
  - "Paste Last Item" menu option respects current paste mode

### CI/CD Status
- ✅ All GitHub Actions passing on all platforms (Ubuntu, Windows, macOS)
- ✅ All Python versions tested (3.9, 3.10, 3.11, 3.12)
- ✅ 241 tests passing with proper timeouts
- ✅ Type checking (mypy) passing on all platforms
- ✅ Code quality checks (ruff) passing
- ✅ Cross-platform compatibility verified

### Next Steps (per PRD)
- [x] Phase 10: Write end-to-end integration tests ✅ (97 tests passing)
- [ ] Phase 10: Implement performance optimizations
- [ ] Phase 10: Write performance benchmarks
- [ ] Phase 11: Platform-specific features (Windows, Linux - macOS mostly done)
- [ ] Phase 12: Documentation and packaging
- [ ] Phase 13: Final testing and release preparation

## Important Reminders

- When running tests, use pytest with timeout to prevent hanging: `uv run pytest --timeout=30`
- For CI/CD issues, check all platforms (Ubuntu, Windows, macOS) separately
- Use skipif markers for platform-specific tests that require modules not available on all platforms
- Always run `uv run ruff check . --fix && uv run ruff format .` before committing
- Test locally with mypy before pushing: `uv run mypy src/`
- Clipboard monitoring should ONLY save to history, never auto-paste
- History should be saved even when monitoring is disabled
- On macOS, ensure dialogs respond to Cmd+W and have proper window controls
