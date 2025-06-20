# Pasta - Cross-Platform Clipboard-to-Keyboard System Tray Application
## Product Requirements Document (PRD)

### Current Status Summary (Updated: 2025-06-19)
- **Core Features**: ✅ All implemented and tested (92% code coverage, 610 tests)
- **Platform Support**: ✅ macOS (most mature), ⚠️ Windows/Linux (basic support)
- **CI/CD**: ✅ All tests passing on all platforms (Python 3.9-3.13)
- **Remaining Work**: Performance optimization, platform-specific polish, user documentation, distribution packaging

### Project Overview
Pasta is a cross-platform system tray application that converts clipboard content into simulated keyboard input, bridging the gap for applications that don't support direct clipboard pasting. The application will be developed using Python with UV package management, following Test-Driven Development (TDD) principles.

### Technology Stack
- **Language**: Python 3.13+ (required for development, 3.9+ supported for runtime)
- **Package Manager**: UV (not pip)
- **System Tray**: PySide6 (QSystemTrayIcon) - replaced pystray for better integration
- **GUI Framework**: PySide6 (Qt6) for all UI components
- **Keyboard Simulation**: PyAutoGUI with osascript fallback on macOS
- **Clipboard Access**: pyperclip
- **Testing**: pytest with pytest-qt
- **Code Quality**: Ruff (includes Black, isort, pylint functionality)
- **Type Checking**: mypy with strict mode
- **Line Length**: 140 characters
- **Build System**: Nix flakes for reproducible environments (macOS)

## Development Task List

### Phase 1: Project Setup and Configuration

- [x] **Install UV package manager**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [x] **Initialize project structure**
  ```bash
  uv init pasta --python 3.11
  mkdir -p src/pasta/{core,gui,utils} tests/{unit,integration,fixtures} scripts docs
  ```

- [x] **Create initial pyproject.toml with all dependencies**
  - Configure project metadata
  - Add core dependencies: pystray, pyperclip, pyautogui, pillow
  - Add dev dependencies: pytest, pytest-qt, pytest-cov, pytest-mock, ruff, mypy, pre-commit
  - Configure Ruff with 140 character line length
  - Configure tool settings for black, isort compatibility

- [x] **Set up pre-commit hooks**
  - Create .pre-commit-config.yaml
  - Configure Ruff for linting and formatting
  - Configure mypy for type checking
  - Run `uv run pre-commit install`

- [x] **Create project scaffolding files**
  - Create src/pasta/__init__.py
  - Create src/pasta/__main__.py with placeholder entry point
  - Create tests/__init__.py
  - Create tests/conftest.py with initial fixtures
  - Create README.md with project description
  - Create LICENSE file (MIT)
  - Create .gitignore with Python defaults

- [x] **Set up GitHub Actions CI/CD**
  - Create .github/workflows/test.yml
  - Configure multi-OS testing (Ubuntu, Windows, macOS)
  - Configure Python version matrix (3.9, 3.10, 3.11, 3.12)
  - Add linting, type checking, and test stages
  - Configure coverage reporting

### Phase 2: Core Module Tests (TDD)

- [x] **Write ClipboardManager tests (tests/unit/test_clipboard.py)**
  - Test clipboard monitoring initialization
  - Test clipboard change detection
  - Test content type detection (text, url, multiline, large_text)
  - Test history management with size limits
  - Test history deduplication
  - Test callback registration and notification
  - Test thread safety

- [x] **Write PastaKeyboardEngine tests (tests/unit/test_keyboard.py)**
  - Test keyboard initialization with platform detection
  - Test paste via clipboard method
  - Test paste via typing method
  - Test large text chunking
  - Test typing speed controls
  - Test fail-safe mechanism
  - Test platform-specific key combinations

- [x] **Write PermissionChecker tests (tests/unit/test_permissions.py)**
  - Test macOS accessibility permission checking
  - Test Windows permission requirements
  - Test Linux input group checking
  - Test permission request methods
  - Test fallback behavior

- [x] **Write StorageManager tests (tests/unit/test_storage.py)**
  - Test SQLite database initialization
  - Test entry saving with encryption
  - Test entry retrieval and decryption
  - Test sensitive data detection
  - Test data cleanup and retention
  - Test query performance

### Phase 3: Core Module Implementation

- [x] **Implement ClipboardManager (src/pasta/core/clipboard.py)**
  - Create class with configurable history size
  - Implement clipboard monitoring thread
  - Implement content change detection using hashing
  - Implement content type detection
  - Implement history management with deduplication
  - Implement callback system for change notifications
  - Add thread safety with locks

- [x] **Implement PastaKeyboardEngine (src/pasta/core/keyboard.py)**
  - Create class with platform detection
  - Implement paste via clipboard method
  - Implement paste via typing method with chunking
  - Implement adaptive typing speed based on system load
  - Implement fail-safe mechanism (mouse to corner)
  - Add platform-specific optimizations

- [x] **Implement PermissionChecker (src/pasta/utils/permissions.py)**
  - Implement macOS accessibility permission check
  - Implement macOS permission request dialog
  - Implement Windows UAC manifest generation
  - Implement Linux permission setup script
  - Add user-friendly error messages

- [x] **Implement StorageManager (src/pasta/core/storage.py)**
  - Implement SQLite database setup
  - Implement secure storage for sensitive data
  - Implement encryption for sensitive entries
  - Implement data retention policies
  - Add indexes for performance

### Phase 4: System Tray Tests

- [x] **Write SystemTray tests (tests/unit/test_tray.py)**
  - Test tray icon creation
  - Test menu structure generation
  - Test menu item visibility conditions
  - Test click handlers
  - Test icon updates
  - Test platform-specific behavior

- [x] **Write integration tests for tray interactions**
  - Test quick paste functionality
  - Test history window triggering
  - Test settings window triggering
  - Test monitoring toggle
  - Test application quit

### Phase 5: System Tray Implementation

- [x] **Implement SystemTray (src/pasta/gui/tray.py)**
  - Create pystray Icon instance
  - Implement platform-specific icon generation
  - Create dynamic menu structure
  - Implement quick paste (default left-click)
  - Implement monitoring toggle
  - Add menu item visibility conditions
  - Implement quit functionality

- [x] **Create tray icons (src/pasta/gui/resources/)**
  - Design platform-specific icons (16x16, 22x22, 32x32)
  - Create template images for macOS
  - Create color icons for Windows/Linux
  - Create status indicator variations

### Phase 6: Settings and UI Tests

- [x] **Write Settings tests (tests/unit/test_settings.py)**
  - Test settings storage and retrieval
  - Test default values
  - Test validation rules
  - Test settings migration
  - Test UI binding

- [x] **Write UI component tests**
  - Test settings window layout
  - Test control interactions
  - Test validation feedback
  - Test save/cancel behavior

### Phase 7: Settings and UI Implementation

- [x] **Implement Settings system (src/pasta/core/settings.py)**
  - Create settings schema with defaults
  - Implement JSON-based storage
  - Add validation for all settings
  - Implement settings migration
  - Add observer pattern for changes

- [x] **Implement Settings UI (src/pasta/gui/settings.py)**
  - Create minimal settings window
  - Add typing speed controls
  - Add history size limit control
  - Add privacy settings
  - Add excluded applications list
  - Implement save/cancel logic

### Phase 8: Advanced Features Tests

- [x] **Write HotkeyManager tests** (Emergency stop implementation)
  - Test global hotkey registration
  - Test hotkey conflict detection
  - Test platform-specific implementations
  - Test cleanup on exit

- [x] **Write SecurityManager tests**
  - Test sensitive data detection patterns
  - Test encryption/decryption
  - Test rate limiting
  - Test privacy mode

- [x] **Write snippet system tests**
  - Test snippet creation
  - Test snippet storage
  - Test snippet retrieval
  - Test snippet pasting

### Phase 9: Advanced Features Implementation

- [x] **Implement HotkeyManager (src/pasta/core/hotkeys.py)** (Emergency stop implementation)
  - Implement global hotkey registration
  - Add platform-specific implementations
  - Implement conflict detection
  - Add proper cleanup

- [x] **Implement SecurityManager (src/pasta/utils/security.py)**
  - Implement sensitive data patterns
  - Add encryption for sensitive clipboard data
  - Implement rate limiting
  - Add privacy mode toggle

- [x] **Implement Snippet system**
  - Create snippet data model
  - Implement snippet storage
  - Add snippet management UI
  - Integrate with paste engine

### Phase 10: Integration and Performance

- [x] **Write end-to-end integration tests**
  - [x] Test complete workflow from copy to history
  - [x] Test clipboard monitoring saves to history
  - [x] Test manual paste from history
  - [x] Test settings changes affecting behavior
  - [x] Test multi-threaded operations
  - [x] 97 integration tests passing with full coverage

- [ ] **Implement performance optimizations**
  - [ ] Add text analysis for optimal paste method
  - [ ] Implement adaptive delays based on system load
  - [ ] Add CPU/memory monitoring for dynamic speed adjustment
  - [ ] Optimize large text handling with smart chunking

- [ ] **Write performance benchmarks**
  - [ ] Benchmark typing speeds across different text sizes
  - [ ] Benchmark clipboard operations latency
  - [ ] Benchmark memory usage patterns
  - [ ] Test with various text sizes (1KB to 10MB)

### Phase 11: Platform-Specific Features

- [x] **Implement macOS-specific features**
  - [x] Create Info.plist for permissions (in pasta.spec)
  - [x] Add macOS menu bar integration with native behavior
  - [x] LSUIElement configuration (no dock icon)
  - [x] Proper app naming ("Pasta" not "python3.11")
  - [x] Cmd+Q/W handling for all dialog windows
  - [x] Window dock behavior and activation policy
  - [x] NSApplication activation policy
  - [x] Qt platform plugin set to "cocoa" for native behavior
  - [x] Fallback to osascript when pyautogui unavailable (Nix)
  - [x] macOS build script for .app bundle creation
  - [ ] Implement template images for better dark mode support
  - [ ] Test with macOS sandboxing and notarization

- [ ] **Implement Windows-specific features**
  - [ ] Create Windows manifest for UAC
  - [ ] Add Windows notification support
  - [ ] Test with Windows 10/11 versions
  - [ ] Handle high DPI displays properly
  - [ ] Windows installer (MSI) creation

- [ ] **Implement Linux-specific features**
  - [ ] Add support for both X11 and Wayland
  - [ ] Implement AppIndicator support
  - [ ] Create .desktop file for application menu
  - [ ] Test on Ubuntu, Fedora, Debian
  - [ ] Create DEB and RPM packages

### Phase 12: Documentation and Packaging

- [x] **Write developer documentation**
  - [x] CLAUDE.md for AI-assisted development
  - [x] current-state.md for project status
  - [x] Comprehensive code docstrings
  - [x] Type hints throughout codebase
  - [ ] API reference documentation
  - [ ] Architecture diagrams
  - [ ] Contributing guide

- [x] **Create build infrastructure**
  - [x] PyInstaller spec file with platform configuration
  - [x] macOS build script (build_macos.py)
  - [x] Nix flake for reproducible builds
  - [x] UV-based dependency management
  - [ ] Windows build script
  - [ ] Linux build script
  - [ ] Code signing configuration

- [ ] **Write user documentation**
  - [ ] Installation guide for each platform
  - [ ] Permissions setup guide with screenshots
  - [ ] Keyboard shortcuts reference
  - [ ] Troubleshooting guide
  - [ ] Feature walkthrough

- [ ] **Prepare for distribution**
  - [ ] Create platform-specific installers (DMG, MSI, DEB/RPM)
  - [ ] Set up automatic updates mechanism
  - [ ] Create release checklist
  - [ ] Set up download/distribution website

### Recent Fixes and Improvements

- [x] **Fixed clipboard monitoring behavior**
  - Removed automatic paste on clipboard change
  - Fixed "v" character paste bug
  - Ensured clipboard history is always saved
  - Added regression tests for clipboard monitoring

- [x] **macOS UI/UX improvements**
  - Implemented LSUIElement (no dock icon)
  - Fixed app name display ("Pasta" not "python3.11")
  - Added Cmd+W support for dialogs
  - Ensured native window controls
  - Created macOS build script

- [x] **Paste mode implementation**
  - Added Auto/Clipboard/Typing modes with visual feedback
  - Icon color changes: orange (typing), blue (clipboard)
  - "Paste Last Item" respects current paste mode
  - Mode persistence across restarts

- [x] **Additional improvements**
  - Emergency stop with double ESC or tray click
  - Concurrent paste handling with proper queueing
  - RLock implementation for thread safety
  - 610 tests with 92% code coverage
  - All CI/CD passing on all platforms

### Phase 13: Final Testing and Polish

- [x] **Security implementation complete**
  - [x] Fernet encryption for sensitive data
  - [x] Pattern-based sensitive data detection
  - [x] Rate limiting implemented (30 pastes/min, 100 reads/min)
  - [x] Privacy mode with app exclusion
  - [x] Secure memory cleanup on exit
  - [ ] External security audit

- [ ] **Perform usability testing**
  - [ ] Beta testing with real users
  - [ ] Test with various clipboard content types
  - [ ] Verify all keyboard shortcuts work
  - [ ] Test error handling and recovery
  - [ ] Validate accessibility features

- [ ] **Final optimizations**
  - [ ] Optimize startup time (<2 seconds)
  - [ ] Reduce memory footprint (<50MB idle)
  - [ ] Profile and optimize hot paths
  - [ ] Implement lazy loading for faster startup

- [ ] **Release preparation**
  - [ ] Update version to 1.0.0
  - [ ] Generate CHANGELOG.md
  - [ ] Create release notes
  - [ ] Tag release in git
  - [ ] Create GitHub release with binaries

## Technical Specifications

### Supported Platforms
- macOS 10.14+ (Mojave and later)
- Windows 10/11
- Linux (Ubuntu 20.04+, Fedora 35+, Debian 11+)

### Python Version
- Development: Python 3.13+ (required for UV and development)
- Runtime minimum: Python 3.9
- CI/CD tested: Python 3.9, 3.10, 3.11, 3.12, 3.13
- All versions passing tests on Ubuntu, Windows, macOS

### Performance Requirements
- Startup time: < 2 seconds
- Memory usage: < 50MB idle
- Typing speed: Up to 1000 characters/second
- Clipboard monitoring interval: 500ms

### Security Requirements
- All sensitive data encrypted at rest
- No network connections
- No telemetry without explicit consent
- Rate limiting on all operations
- Secure cleanup on exit

---

## Appendix: Detailed Technical Guide

## 1. System Tray/Menu Bar Libraries

### Primary Recommendation: pystray

**pystray** is the optimal cross-platform solution, offering native integration across all platforms with minimal dependencies.

**Key Features:**
- Cross-platform support: Windows (native API), macOS (NSStatusBar), Linux (AppIndicator/GTK+)
- Active maintenance: Version 0.19.5 (September 2023)
- Minimal dependencies: Only requires Pillow
- Clean, purpose-built API for system tray applications

**Implementation Example:**
```python
import pystray
from PIL import Image
import threading

class PastaSystemTray:
    def __init__(self, keyboard_engine, clipboard_manager):
        self.keyboard_engine = keyboard_engine
        self.clipboard_manager = clipboard_manager
        self.icon = None

    def create_icon(self):
        # Create platform-appropriate icon
        size = (64, 64)  # Will be scaled automatically
        image = Image.new('RGB', size, 'white')
        # Add your icon drawing code
        return image

    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Quick Paste", self.quick_paste, default=True),
            pystray.MenuItem("Paste from History...", self.show_history),
            pystray.MenuItem(pystray.Menu.SEPARATOR),
            pystray.MenuItem("Snippets", pystray.Menu(
                pystray.MenuItem("Manage", self.manage_snippets),
                pystray.MenuItem("Create New", self.create_snippet),
            )),
            pystray.MenuItem(pystray.Menu.SEPARATOR),
            pystray.MenuItem("Settings", self.show_settings),
            pystray.MenuItem("Quit", self.quit_app)
        )

    def run(self):
        self.icon = pystray.Icon(
            "pasta",
            self.create_icon(),
            "Pasta - Clipboard Manager",
            self.create_menu()
        )
        self.icon.run()
```

### Complex UI Support: PyQt6/PySide6 Integration

For settings windows and rich interfaces beyond the system tray:

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
import sys

class HybridPastaApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray
        self.setup_tray()  # pystray for tray
        self.settings_window = None  # Qt for windows

    def show_settings(self):
        if not self.settings_window:
            self.settings_window = SettingsWindow()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
```

## 2. Keyboard Simulation Libraries

### Recommended: PyAutoGUI

**PyAutoGUI** provides the most stable cross-platform keyboard simulation with excellent reliability.

**Optimized Implementation:**
```python
import pyautogui
import pyperclip
import time
import platform

class PastaKeyboardEngine:
    def __init__(self):
        # Optimize for speed
        pyautogui.PAUSE = 0.01  # Reduce from default 0.1s
        pyautogui.FAILSAFE = True  # Safety feature

        # Platform-specific settings
        self.is_mac = platform.system() == 'Darwin'
        self.paste_key = 'cmd' if self.is_mac else 'ctrl'

    def paste_text(self, text: str, method: str = 'auto') -> bool:
        """
        Paste text using optimal method

        Args:
            text: Text to paste
            method: 'clipboard', 'typing', or 'auto'
        """
        try:
            if method == 'auto':
                method = 'clipboard' if len(text) < 5000 else 'typing'

            if method == 'clipboard':
                return self._paste_via_clipboard(text)
            else:
                return self._paste_via_typing(text)

        except Exception as e:
            print(f"Paste failed: {e}")
            return False

    def _paste_via_clipboard(self, text: str) -> bool:
        """Fast paste using system clipboard"""
        original = pyperclip.paste()  # Store original
        try:
            pyperclip.copy(text)
            pyautogui.hotkey(self.paste_key, 'v')
            return True
        finally:
            # Optionally restore original clipboard
            time.sleep(0.1)
            pyperclip.copy(original)

    def _paste_via_typing(self, text: str) -> bool:
        """Reliable character-by-character typing"""
        chunk_size = 200

        for i in range(0, len(text), chunk_size):
            if not self._check_continue():  # Safety check
                return False

            chunk = text[i:i+chunk_size]
            pyautogui.write(chunk, interval=0.005)

            # Pause between chunks
            if i + chunk_size < len(text):
                time.sleep(0.05)

        return True

    def _check_continue(self) -> bool:
        """Check if we should continue (fail-safe)"""
        x, y = pyautogui.position()
        return not (x == 0 and y == 0)  # Top-left corner abort
```

### Performance Optimization

```python
import psutil
from typing import Optional

class AdaptiveTypingEngine:
    """Adjusts typing speed based on system performance"""

    def __init__(self):
        self.base_interval = 0.005
        self.max_interval = 0.05
        self.last_cpu_check = 0
        self.cpu_threshold = 70

    def get_typing_interval(self) -> float:
        """Calculate optimal typing interval"""
        current_time = time.time()

        # Check CPU every 2 seconds
        if current_time - self.last_cpu_check > 2:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.last_cpu_check = current_time

            if cpu_percent > self.cpu_threshold:
                return self.max_interval
            else:
                # Scale interval based on CPU usage
                scale = cpu_percent / 100.0
                return self.base_interval + (self.max_interval - self.base_interval) * scale

        return self.base_interval
```

## 3. Clipboard Access Libraries

### Standard: pyperclip

**pyperclip** remains the best choice for cross-platform clipboard access.

**Enhanced Clipboard Manager:**
```python
import pyperclip
import threading
import hashlib
from datetime import datetime
from typing import Callable, Optional, List

class ClipboardManager:
    def __init__(self, history_size: int = 100):
        self.history: List[dict] = []
        self.history_size = history_size
        self.monitoring = False
        self.callbacks: List[Callable] = []
        self._last_hash = ""

    def start_monitoring(self):
        """Start monitoring clipboard for changes"""
        if self.monitoring:
            return

        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                content = pyperclip.paste()
                content_hash = hashlib.md5(content.encode()).hexdigest()

                if content_hash != self._last_hash and content.strip():
                    self._last_hash = content_hash

                    # Add to history
                    entry = {
                        'content': content,
                        'timestamp': datetime.now(),
                        'hash': content_hash,
                        'type': self._detect_content_type(content)
                    }

                    self._add_to_history(entry)

                    # Notify callbacks
                    for callback in self.callbacks:
                        callback(entry)

            except Exception as e:
                print(f"Clipboard monitoring error: {e}")

            time.sleep(0.5)

    def _detect_content_type(self, content: str) -> str:
        """Detect type of clipboard content"""
        if content.startswith(('http://', 'https://')):
            return 'url'
        elif '\t' in content or '\n' in content:
            return 'multiline'
        elif len(content) > 500:
            return 'large_text'
        else:
            return 'text'

    def _add_to_history(self, entry: dict):
        """Add entry to history with deduplication"""
        # Remove duplicates
        self.history = [e for e in self.history if e['hash'] != entry['hash']]

        # Add new entry
        self.history.insert(0, entry)

        # Trim history
        if len(self.history) > self.history_size:
            self.history = self.history[:self.history_size]

    def register_callback(self, callback: Callable):
        """Register callback for clipboard changes"""
        self.callbacks.append(callback)
```

## 4. System Permission Requirements

### macOS Accessibility Setup

**Automated Permission Check:**
```python
import subprocess
import platform
import os

class MacOSPermissions:
    @staticmethod
    def check_accessibility() -> bool:
        """Check if app has accessibility permissions"""
        if platform.system() != 'Darwin':
            return True

        script = '''
        tell application "System Events"
            set isEnabled to UI elements enabled
        end tell
        return isEnabled
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        return result.stdout.strip() == 'true'

    @staticmethod
    def request_accessibility():
        """Open accessibility preferences"""
        script = '''
        tell application "System Preferences"
            activate
            reveal anchor "Privacy_Accessibility" of pane id "com.apple.preference.security"
        end tell
        '''
        subprocess.run(['osascript', '-e', script])

    @staticmethod
    def create_info_plist():
        """Generate Info.plist content"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Pasta</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.pasta</string>
    <key>NSAccessibilityUsageDescription</key>
    <string>Pasta requires accessibility permissions to simulate keyboard input.</string>
</dict>
</plist>"""
```

### Windows UAC Configuration

```python
class WindowsPermissions:
    @staticmethod
    def create_manifest():
        """Generate Windows manifest for UAC"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>"""
```

### Linux Permission Setup

```python
class LinuxPermissions:
    @staticmethod
    def check_wayland() -> bool:
        """Check if running under Wayland"""
        return os.environ.get('XDG_SESSION_TYPE') == 'wayland'

    @staticmethod
    def setup_permissions():
        """Setup script for Linux permissions"""
        script = """#!/bin/bash
# Add user to input group for device access
sudo usermod -a -G input $USER

# Install required packages
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "Installing Wayland tools..."
    sudo apt-get install -y ydotool
else
    echo "Installing X11 tools..."
    sudo apt-get install -y xdotool xclip
fi

echo "Please log out and back in for group changes to take effect."
"""
        return script
```

## 5. Test-Driven Development with pytest

### Comprehensive Testing Setup

**conftest.py:**
```python
import pytest
import sys
import os
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_clipboard(monkeypatch):
    """Mock clipboard operations"""
    clipboard_content = [""]

    def mock_copy(text):
        clipboard_content[0] = text

    def mock_paste():
        return clipboard_content[0]

    monkeypatch.setattr("pyperclip.copy", mock_copy)
    monkeypatch.setattr("pyperclip.paste", mock_paste)

    return clipboard_content

@pytest.fixture
def mock_keyboard(monkeypatch):
    """Mock keyboard operations"""
    typed_text = []

    def mock_write(text, interval=0):
        typed_text.append(text)

    def mock_hotkey(*keys):
        typed_text.append(f"hotkey:{'+'.join(keys)}")

    monkeypatch.setattr("pyautogui.write", mock_write)
    monkeypatch.setattr("pyautogui.hotkey", mock_hotkey)

    return typed_text

@pytest.fixture
def pasta_app(qtbot):
    """Create Pasta application for testing"""
    from pasta.gui.main import PastaApp
    app = PastaApp(test_mode=True)
    qtbot.addWidget(app)
    return app
```

**Test Examples:**
```python
import pytest
from pasta.core.keyboard import PastaKeyboardEngine

class TestKeyboardEngine:
    def test_clipboard_paste(self, mock_clipboard, mock_keyboard):
        """Test paste via clipboard method"""
        engine = PastaKeyboardEngine()

        success = engine.paste_text("Hello World", method='clipboard')

        assert success
        assert mock_clipboard[0] == "Hello World"
        assert "hotkey:ctrl+v" in mock_keyboard or "hotkey:cmd+v" in mock_keyboard

    def test_typing_paste(self, mock_keyboard):
        """Test paste via typing method"""
        engine = PastaKeyboardEngine()

        success = engine.paste_text("Test", method='typing')

        assert success
        assert "Test" in "".join(mock_keyboard)

    def test_large_text_chunking(self, mock_keyboard):
        """Test large text is chunked properly"""
        engine = PastaKeyboardEngine()
        large_text = "x" * 1000

        success = engine.paste_text(large_text, method='typing')

        assert success
        # Verify text was sent in chunks
        assert len(mock_keyboard) > 1

class TestClipboardManager:
    def test_clipboard_monitoring(self, mock_clipboard):
        """Test clipboard change detection"""
        from pasta.core.clipboard import ClipboardManager

        manager = ClipboardManager()
        changes = []

        manager.register_callback(lambda entry: changes.append(entry))
        manager.start_monitoring()

        # Simulate clipboard change
        mock_clipboard[0] = "New content"

        # Wait for detection
        import time
        time.sleep(1)

        assert len(changes) > 0
        assert changes[0]['content'] == "New content"

    def test_history_deduplication(self):
        """Test duplicate entries are removed"""
        from pasta.core.clipboard import ClipboardManager

        manager = ClipboardManager(history_size=10)

        # Add same content twice
        entry1 = {'content': 'test', 'hash': 'abc123', 'timestamp': None, 'type': 'text'}
        entry2 = {'content': 'test', 'hash': 'abc123', 'timestamp': None, 'type': 'text'}

        manager._add_to_history(entry1)
        manager._add_to_history(entry2)

        assert len(manager.history) == 1
```

### CI/CD Configuration

**GitHub Actions (.github/workflows/test.yml):**
```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4

    - name: Install UV
      uses: astral-sh/setup-uv@v3
      with:
        version: "latest"

    - name: Set up Python
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        uv sync --all-extras --dev

    - name: Run linting
      run: |
        uv run ruff check .
        uv run ruff format --check .

    - name: Run type checking
      run: |
        uv run mypy src/

    - name: Run tests with coverage
      run: |
        uv run pytest -v --cov=pasta --cov-report=xml --cov-report=term-missing
      env:
        QT_QPA_PLATFORM: offscreen  # Headless GUI testing

    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests-${{ matrix.os }}-py${{ matrix.python-version }}
```

## 6. UV Package Manager Setup

### Project Initialization

```bash
# Install UV (10-100x faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
uv init pasta --python 3.11

# Add dependencies
uv add pystray pyperclip pyautogui pillow "PyQt6>=6.4"
uv add --dev pytest pytest-qt pytest-cov black ruff mypy pre-commit
```

### Complete pyproject.toml

```toml
[project]
name = "pasta"
version = "0.1.0"
description = "Cross-platform clipboard to keyboard system tray application"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["clipboard", "productivity", "system-tray", "automation"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "pystray>=0.19.0",
    "pyperclip>=1.8.0",
    "pyautogui>=0.9.50",
    "pillow>=10.0.0",
    "PyQt6>=6.4.0",
    "psutil>=5.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-qt>=4.2.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0",
]

[project.scripts]
pasta = "pasta.__main__:main"

[project.gui-scripts]
pasta-gui = "pasta.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-qt>=4.2.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/pasta"]
```

## 7. Project Structure and Code Quality

### Optimal Project Layout

```
pasta/
├── src/
│   └── pasta/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── clipboard.py     # ClipboardManager
│       │   ├── keyboard.py      # PastaKeyboardEngine
│       │   ├── storage.py       # SQLite history storage
│       │   └── hotkeys.py       # Global hotkey registration
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── tray.py         # System tray (pystray)
│       │   ├── settings.py     # Settings window (Qt)
│       │   ├── history.py      # History browser (Qt)
│       │   └── resources/      # Icons, images
│       └── utils/
│           ├── __init__.py
│           ├── platform.py     # Platform-specific code
│           ├── permissions.py  # Permission checking
│           └── security.py     # Security utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_clipboard.py
│   │   ├── test_keyboard.py
│   │   └── test_storage.py
│   ├── integration/
│   │   ├── test_gui_integration.py
│   │   └── test_system_integration.py
│   └── fixtures/
│       └── test_data.py
├── scripts/
│   ├── build_windows.py
│   ├── build_macos.py
│   └── build_linux.py
├── docs/
│   ├── installation.md
│   ├── permissions.md
│   └── api.md
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── build.yml
│       └── release.yml
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── LICENSE
└── uv.lock
```

### Code Quality Configuration

**Ruff Configuration (pyproject.toml):**
```toml
[tool.ruff]
target-version = "py39"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
]
ignore = [
    "E501",  # line length (handled by formatter)
    "B008",  # function calls in argument defaults
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*" = ["S101", "ARG", "PLR2004"]

[tool.ruff.lint.isort]
known-first-party = ["pasta"]
```

**Pre-commit Configuration (.pre-commit-config.yaml):**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-toml
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
```

**Type Hints Example:**
```python
from typing import Optional, List, Dict, Protocol, TypedDict
from datetime import datetime

class ClipboardEntry(TypedDict):
    content: str
    timestamp: datetime
    hash: str
    type: str

class StorageProtocol(Protocol):
    def save_entry(self, entry: ClipboardEntry) -> int: ...
    def get_entries(self, limit: int) -> List[ClipboardEntry]: ...
    def delete_entry(self, entry_id: int) -> bool: ...

class PastaCore:
    def __init__(
        self,
        storage: StorageProtocol,
        keyboard_engine: Optional[PastaKeyboardEngine] = None,
        clipboard_manager: Optional[ClipboardManager] = None
    ) -> None:
        self.storage = storage
        self.keyboard = keyboard_engine or PastaKeyboardEngine()
        self.clipboard = clipboard_manager or ClipboardManager()
```

## 8. UX Design Patterns

### System Tray Menu Design

```python
def create_optimal_menu():
    """Create user-friendly system tray menu"""
    return pystray.Menu(
        # Primary action (left-click default)
        pystray.MenuItem(
            "📋 Quick Paste Last Item",
            quick_paste_last,
            default=True,
            visible=lambda item: has_clipboard_history()
        ),

        # Frequent actions
        pystray.MenuItem("📝 Paste from History...", show_history_window),
        pystray.MenuItem("✂️ Snippets", pystray.Menu(
            pystray.MenuItem("Browse Snippets", browse_snippets),
            pystray.MenuItem("Create Snippet from Clipboard", create_snippet),
            pystray.MenuItem(pystray.Menu.SEPARATOR),
            # Dynamic snippet list
            lambda: [
                pystray.MenuItem(s.name, lambda: paste_snippet(s))
                for s in get_recent_snippets(5)
            ]
        )),

        pystray.MenuItem(pystray.Menu.SEPARATOR),

        # Status and settings
        pystray.MenuItem(
            lambda item: f"⏸️ Monitoring: {'On' if is_monitoring() else 'Off'}",
            toggle_monitoring
        ),
        pystray.MenuItem("⚙️ Settings...", show_settings),

        pystray.MenuItem(pystray.Menu.SEPARATOR),

        # Help and exit
        pystray.MenuItem("❓ Help", show_help),
        pystray.MenuItem("🚪 Quit Pasta", quit_application)
    )
```

### Platform-Specific Icon Guidelines

```python
import platform
from PIL import Image, ImageDraw

def create_platform_icon() -> Image.Image:
    """Create platform-appropriate tray icon"""
    system = platform.system()

    if system == "Darwin":  # macOS
        # Template image: black and white only
        size = (22, 22)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Simple clipboard icon
        draw.rectangle([4, 2, 18, 20], fill='black')
        draw.rectangle([6, 4, 16, 18], fill='white')
        draw.rectangle([8, 6, 14, 8], fill='black')
        draw.rectangle([8, 10, 14, 12], fill='black')

        return image

    else:  # Windows/Linux
        # Full color icon
        size = (16, 16) if system == "Windows" else (22, 22)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Colorful clipboard icon
        draw.rectangle([2, 1, 14, 15], fill='#4CAF50')
        draw.rectangle([3, 2, 13, 14], fill='white')
        draw.rectangle([5, 4, 11, 6], fill='#2196F3')
        draw.rectangle([5, 8, 11, 10], fill='#2196F3')

        return image
```

## 9. Performance Optimization

### Intelligent Text Processing

```python
class SmartPasteEngine:
    """Intelligently handle different text types and sizes"""

    def __init__(self):
        self.clipboard_threshold = 5000  # Characters
        self.chunk_size = 200
        self.adaptive_delay = AdaptiveDelay()

    def paste(self, text: str) -> bool:
        """Smart paste with automatic method selection"""
        text_type = self._analyze_text(text)

        if text_type == 'code':
            return self._paste_code(text)
        elif text_type == 'formatted':
            return self._paste_formatted(text)
        elif len(text) > self.clipboard_threshold:
            return self._paste_large(text)
        else:
            return self._paste_standard(text)

    def _analyze_text(self, text: str) -> str:
        """Analyze text type for optimal pasting"""
        if any(indicator in text for indicator in ['def ', 'class ', 'function', '{}', '();']):
            return 'code'
        elif '\t' in text or text.count('\n') > 10:
            return 'formatted'
        else:
            return 'standard'

    def _paste_code(self, text: str) -> bool:
        """Paste code with proper formatting preservation"""
        # Use clipboard to preserve formatting
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        return True

    def _paste_large(self, text: str) -> bool:
        """Efficiently paste large text"""
        lines = text.split('\n')

        for i, line in enumerate(lines):
            pyautogui.write(line, interval=0.001)

            if i < len(lines) - 1:
                pyautogui.press('enter')

            # Adaptive delay based on system load
            if i % 10 == 0:
                time.sleep(self.adaptive_delay.get_delay())

        return True

class AdaptiveDelay:
    """Dynamically adjust delays based on system performance"""

    def __init__(self):
        self.min_delay = 0.001
        self.max_delay = 0.1
        self.cpu_threshold = 70

    def get_delay(self) -> float:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent

        # Calculate stress factor (0-1)
        stress = (cpu_percent / 100 * 0.7) + (memory_percent / 100 * 0.3)

        # Scale delay based on stress
        delay = self.min_delay + (self.max_delay - self.min_delay) * stress

        return min(delay, self.max_delay)
```

## 10. Security Best Practices

### Comprehensive Security Implementation

```python
import hashlib
import secrets
from cryptography.fernet import Fernet
from typing import Optional
import re

class SecureClipboardStorage:
    """Secure storage for sensitive clipboard data"""

    def __init__(self, encryption_key: Optional[bytes] = None):
        self.key = encryption_key or self._generate_key()
        self.cipher = Fernet(self.key)
        self.sensitive_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',          # SSN
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',  # Email
            r'(?i)(password|passwd|pwd)[\s:=]+\S+',  # Passwords
            r'(?i)(api[_-]?key|secret)[\s:=]+\S+',   # API keys
        ]

    def _generate_key(self) -> bytes:
        """Generate encryption key"""
        return Fernet.generate_key()

    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive data"""
        for pattern in self.sensitive_patterns:
            if re.search(pattern, text):
                return True
        return False

    def store_entry(self, content: str, metadata: dict) -> dict:
        """Store clipboard entry with encryption if sensitive"""
        entry = {
            'timestamp': datetime.now(),
            'hash': hashlib.sha256(content.encode()).hexdigest(),
            'metadata': metadata
        }

        if self.is_sensitive(content):
            entry['content'] = self.cipher.encrypt(content.encode()).decode()
            entry['encrypted'] = True
        else:
            entry['content'] = content
            entry['encrypted'] = False

        return entry

    def retrieve_content(self, entry: dict) -> str:
        """Retrieve and decrypt content if necessary"""
        if entry.get('encrypted'):
            return self.cipher.decrypt(entry['content'].encode()).decode()
        return entry['content']

class RateLimiter:
    """Prevent abuse and system overload"""

    def __init__(self):
        self.limits = {
            'paste': (30, 60),      # 30 pastes per 60 seconds
            'clipboard': (100, 60),  # 100 clipboard reads per 60 seconds
            'large_paste': (5, 300)  # 5 large pastes per 5 minutes
        }
        self.history = defaultdict(list)

    def is_allowed(self, action: str, size: Optional[int] = None) -> bool:
        """Check if action is allowed under rate limits"""
        if size and size > 10000:
            action = 'large_paste'

        if action not in self.limits:
            return True

        max_count, window_seconds = self.limits[action]
        now = time.time()
        cutoff = now - window_seconds

        # Clean old entries
        self.history[action] = [
            t for t in self.history[action] if t > cutoff
        ]

        if len(self.history[action]) >= max_count:
            return False

        self.history[action].append(now)
        return True

class PrivacyProtection:
    """Implement privacy protection features"""

    def __init__(self):
        self.excluded_apps = set()
        self.excluded_patterns = []
        self.privacy_mode = False

    def should_capture(self, active_window: str, content: str) -> bool:
        """Determine if content should be captured"""
        if self.privacy_mode:
            return False

        # Check excluded applications
        if any(app in active_window.lower() for app in self.excluded_apps):
            return False

        # Check excluded patterns
        for pattern in self.excluded_patterns:
            if re.search(pattern, content):
                return False

        return True

    def add_excluded_app(self, app_name: str):
        """Add app to exclusion list"""
        self.excluded_apps.add(app_name.lower())

    def add_excluded_pattern(self, pattern: str):
        """Add regex pattern to exclude"""
        try:
            re.compile(pattern)
            self.excluded_patterns.append(pattern)
        except re.error:
            raise ValueError(f"Invalid regex pattern: {pattern}")
```

### User Consent and Transparency

```python
class ConsentManager:
    """Manage user consent and privacy preferences"""

    def __init__(self):
        self.consent_file = Path.home() / '.pasta' / 'consent.json'
        self.consent_file.parent.mkdir(exist_ok=True)
        self.consents = self._load_consents()

    def _load_consents(self) -> dict:
        """Load saved consent preferences"""
        if self.consent_file.exists():
            with open(self.consent_file, 'r') as f:
                return json.load(f)
        return {}

    def check_first_run(self) -> bool:
        """Check if this is first run"""
        return 'initial_consent' not in self.consents

    def show_privacy_dialog(self) -> bool:
        """Show privacy information dialog"""
        from PyQt6.QtWidgets import QMessageBox, QCheckBox

        msg = QMessageBox()
        msg.setWindowTitle("Pasta - Privacy Information")
        msg.setText(
            "Pasta needs certain permissions to function:\n\n"
            "• Monitor clipboard for content\n"
            "• Simulate keyboard input\n"
            "• Store clipboard history locally\n\n"
            "Your data:\n"
            "• Is processed locally only\n"
            "• Is never sent to external servers\n"
            "• Can be cleared at any time\n\n"
            "Do you agree to these terms?"
        )

        # Add checkboxes for optional features
        analytics_cb = QCheckBox("Share anonymous usage statistics")
        msg.setCheckBox(analytics_cb)

        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        result = msg.exec()

        if result == QMessageBox.Yes:
            self.consents['initial_consent'] = True
            self.consents['analytics'] = analytics_cb.isChecked()
            self.consents['timestamp'] = datetime.now().isoformat()
            self._save_consents()
            return True

        return False

    def _save_consents(self):
        """Save consent preferences"""
        with open(self.consent_file, 'w') as f:
            json.dump(self.consents, f, indent=2)
```

## Development Workflow Commands

### Quick Reference

```bash
# Setup development environment
uv sync --all-extras
uv run pre-commit install

# Run development server
uv run python -m pasta

# Code quality checks
uv run ruff check . --fix
uv run ruff format .
uv run mypy src/

# Testing
uv run pytest
uv run pytest --cov=pasta --cov-report=html
uv run pytest -k "test_clipboard" -v  # Run specific tests

# Build for distribution
uv build

# Create platform-specific executables
uv run pyinstaller --onefile --windowed src/pasta/__main__.py
```

## Conclusion

This comprehensive guide provides everything needed to develop Pasta as a professional, cross-platform clipboard management application. The recommended stack of:

- **pystray** for system tray functionality
- **PyAutoGUI** for reliable keyboard simulation
- **pyperclip** for clipboard access
- **UV** for modern package management
- **pytest** with pytest-qt for comprehensive testing
- **Ruff** for fast, modern linting

offers the optimal balance of performance, reliability, and maintainability. The architecture supports easy extension while maintaining security and user privacy as core principles.

Key success factors:
1. Platform-specific permission handling is critical
2. Performance optimization prevents system lag
3. Security measures protect user data
4. Clean UX patterns ensure usability
5. Comprehensive testing ensures reliability
6. Modern tooling improves developer experience

With this foundation, Pasta can deliver a professional clipboard management experience across Windows, macOS, and Linux platforms.
