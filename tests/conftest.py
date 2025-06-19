"""Pytest configuration and shared fixtures."""

import contextlib
import os
import signal
import subprocess
import sys
import time
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

# Set Qt to run in offscreen mode for all tests to prevent GUI windows
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure tests don't open real system dialogs
os.environ["PASTA_TESTING"] = "1"

# Mock the keyboard module to prevent import failures in test environments
# This is necessary because the keyboard module can fail on some systems
# (e.g., macOS without proper permissions, headless environments, etc.)
keyboard_mock = MagicMock()
keyboard_mock.add_hotkey = MagicMock()
keyboard_mock.remove_hotkey = MagicMock()
keyboard_mock.unhook_all = MagicMock()
keyboard_mock.is_pressed = MagicMock(return_value=False)
sys.modules["keyboard"] = keyboard_mock

# Mock pyautogui globally to prevent any actual keyboard/mouse interaction
pyautogui_mock = MagicMock()
pyautogui_mock.FAILSAFE = False
pyautogui_mock.PAUSE = 0
pyautogui_mock.write = MagicMock()
pyautogui_mock.typewrite = MagicMock()
pyautogui_mock.press = MagicMock()
pyautogui_mock.hotkey = MagicMock()
pyautogui_mock.click = MagicMock()
pyautogui_mock.moveTo = MagicMock()
pyautogui_mock.position = MagicMock(return_value=(0, 0))
pyautogui_mock.screenshot = MagicMock()
pyautogui_mock.keyDown = MagicMock()
pyautogui_mock.keyUp = MagicMock()
sys.modules["pyautogui"] = pyautogui_mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def kill_existing_pasta_processes():
    """Kill any existing Pasta processes to prevent test interference."""
    # Skip entirely in CI environment to avoid killing test infrastructure
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        return

    # Different process names to check
    process_names = ["pasta", "Pasta", "python -m pasta", "pasta.app"]

    if sys.platform == "darwin":  # macOS
        for name in process_names:
            with contextlib.suppress(subprocess.SubprocessError):
                # Use pkill to find and kill processes
                subprocess.run(["pkill", "-f", name], capture_output=True, text=True)

        # Also check for the app bundle
        with contextlib.suppress(subprocess.SubprocessError):
            # Kill by app bundle identifier if running as .app
            subprocess.run(["pkill", "-f", "pasta.app/Contents/MacOS/pasta"], capture_output=True, text=True)

    elif sys.platform == "win32":  # Windows
        for name in process_names:
            with contextlib.suppress(subprocess.SubprocessError):
                # Use taskkill to find and kill processes
                subprocess.run(["taskkill", "/F", "/IM", f"{name}.exe"], capture_output=True, text=True)

    else:  # Linux and others
        for name in process_names:
            with contextlib.suppress(subprocess.SubprocessError):
                # Use pkill to find and kill processes
                subprocess.run(["pkill", "-f", name], capture_output=True, text=True)

    # Also try to find Python processes running pasta module
    try:
        if sys.platform == "win32":
            # Windows: find python processes with pasta in command line
            result = subprocess.run(
                ["wmic", "process", "where", "name='python.exe'", "get", "processid,commandline"], capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "pasta" in line.lower() and "__main__" in line:
                        # Don't kill test processes
                        if any(skip in line.lower() for skip in ["pytest", "test", "coverage"]):
                            continue
                        # Extract PID from line
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            if pid.isdigit():
                                with contextlib.suppress(subprocess.SubprocessError):
                                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            # Unix-like: use ps and grep
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "python" in line and ("pasta" in line or "pasta/__main__.py" in line):
                        # Don't kill the test runner itself or CI processes
                        if any(skip in line for skip in ["pytest", "xvfb", "coverage", "cov", "test"]):
                            continue
                        # Only kill if it's actually running the pasta module
                        if "-m pasta" in line or "pasta/__main__.py" in line:
                            # Extract PID (second column)
                            parts = line.split()
                            if len(parts) > 1:
                                pid = parts[1]
                                if pid.isdigit():
                                    with contextlib.suppress(ProcessLookupError, PermissionError):
                                        os.kill(int(pid), signal.SIGTERM)
    except Exception:
        # Silently ignore any errors
        pass

    # Wait a moment for processes to terminate
    time.sleep(0.5)


@pytest.fixture(scope="session", autouse=True)
def ensure_no_pasta_running():
    """Ensure no Pasta instances are running before tests start."""
    print("\n🔍 Checking for existing Pasta processes...")
    kill_existing_pasta_processes()
    print("✅ Ready to run tests")

    yield

    # Optionally kill again after tests (in case tests leave processes running)
    kill_existing_pasta_processes()


@pytest.fixture(scope="function")
def cleanup_pasta_processes():
    """Fixture to kill Pasta processes before and after individual tests that launch the app."""
    # Kill before test
    kill_existing_pasta_processes()

    yield

    # Kill after test
    kill_existing_pasta_processes()


@pytest.fixture
def mock_clipboard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Mock clipboard operations.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        List containing clipboard content (mutable for testing)
    """
    clipboard_content = [""]

    def mock_copy(text: str) -> None:
        clipboard_content[0] = text

    def mock_paste() -> str:
        return clipboard_content[0]

    monkeypatch.setattr("pyperclip.copy", mock_copy)
    monkeypatch.setattr("pyperclip.paste", mock_paste)

    return clipboard_content


@pytest.fixture
def mock_keyboard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Mock keyboard operations.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        List containing typed text (mutable for testing)
    """
    typed_text: list[str] = []

    def mock_write(text: str, interval: float = 0) -> None:
        typed_text.append(text)

    def mock_hotkey(*keys: str) -> None:
        typed_text.append(f"hotkey:{'+'.join(keys)}")

    def mock_press(key: str) -> None:
        typed_text.append(f"press:{key}")

    monkeypatch.setattr("pyautogui.write", mock_write)
    monkeypatch.setattr("pyautogui.hotkey", mock_hotkey)
    monkeypatch.setattr("pyautogui.press", mock_press)

    return typed_text


@pytest.fixture
def mock_position(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock mouse position.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock object for position function
    """
    position_mock = Mock(return_value=(100, 100))
    monkeypatch.setattr("pyautogui.position", position_mock)
    return position_mock


@pytest.fixture
def temp_db_path(tmp_path: Any) -> str:
    """Create temporary database path.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary database file
    """
    return str(tmp_path / "test_pasta.db")


@pytest.fixture
def mock_platform(monkeypatch: pytest.MonkeyPatch) -> Generator[Mock]:
    """Mock platform detection.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Yields:
        Mock object for platform.system
    """
    platform_mock = Mock(return_value="Darwin")  # Default to macOS
    monkeypatch.setattr("platform.system", platform_mock)
    yield platform_mock


@pytest.fixture(autouse=True)
def no_gui_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable actual GUI operations during tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Mock PyAutoGUI safety features
    monkeypatch.setattr("pyautogui.FAILSAFE", False)
    monkeypatch.setattr("pyautogui.PAUSE", 0)

    # Mock GUI screenshot to prevent actual screenshots
    monkeypatch.setattr("pyautogui.screenshot", Mock())


@pytest.fixture
def mock_time(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock time functions for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Mock object for time functions
    """
    time_mock = Mock()
    time_mock.time.return_value = 1234567890.0
    time_mock.sleep = Mock()

    monkeypatch.setattr("time.time", time_mock.time)
    monkeypatch.setattr("time.sleep", time_mock.sleep)

    return time_mock


@pytest.fixture(autouse=True)
def reset_keyboard_mock():
    """Reset keyboard mock before each test."""
    keyboard_mock.reset_mock()
    keyboard_mock.add_hotkey.reset_mock()
    keyboard_mock.remove_hotkey.reset_mock()
    yield


@pytest.fixture(autouse=True)
def mock_permission_checker_subprocess(monkeypatch: pytest.MonkeyPatch, request) -> None:
    """Mock subprocess calls in PermissionChecker to prevent system dialogs.

    This is applied automatically to all tests to ensure no test accidentally
    opens System Preferences or makes actual system calls.
    """
    # Skip this fixture for unit tests that need to test subprocess behavior
    if "test_permissions" in str(request.fspath) and "unit" in str(request.fspath):
        # Unit tests handle their own mocking
        return

    import subprocess

    original_run = subprocess.run

    def mock_subprocess_run(cmd, *args, **kwargs):
        """Mock subprocess.run to intercept permission-related calls."""
        # Check if this is a permission-related call
        if isinstance(cmd, list) and len(cmd) > 0:
            # macOS osascript calls for checking/requesting permissions
            if "osascript" in cmd[0]:
                # Check if it's checking UI elements enabled
                if any("UI elements enabled" in str(arg) for arg in cmd):
                    # Return True for permission check
                    return Mock(stdout="true\n", returncode=0)
                # Check if it's opening System Preferences
                elif any("System Preferences" in str(arg) for arg in cmd):
                    # Don't actually open System Preferences
                    return Mock(returncode=0)
            # Windows/Linux permission-related calls
            elif any(name in cmd[0] for name in ["pkill", "taskkill", "ps"]):
                # Allow process management calls from conftest
                return original_run(cmd, *args, **kwargs)

        # For any other subprocess calls, return a safe mock
        return Mock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)


# Qt-specific configuration
def pytest_configure(config):
    """Configure pytest for Qt testing."""
    # Set Qt to use offscreen platform for headless testing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Disable Qt accessibility features that might interfere
    os.environ["QT_ACCESSIBILITY"] = "0"

    # Set a consistent Qt style
    os.environ["QT_STYLE_OVERRIDE"] = "fusion"


# Add markers
def pytest_collection_modifyitems(config, items):
    """Add markers to test items."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Mark tests that require display
        if "gui" in item.name or "window" in item.name or "tray" in item.name:
            item.add_marker(pytest.mark.gui)


@pytest.fixture(autouse=True)
def mock_system_calls(monkeypatch):
    """Automatically mock system calls that could interfere with the host system.

    This fixture runs for ALL tests to prevent:
    - Opening System Preferences
    - Executing AppleScript commands
    - Any subprocess calls that could affect the system
    """
    original_subprocess_run = subprocess.run

    def mock_subprocess_run(cmd, *args, **kwargs):
        """Mock subprocess.run to prevent system interference."""
        # Check if this is a command that would open system preferences or execute AppleScript
        if isinstance(cmd, list) and len(cmd) > 0:
            cmd_str = " ".join(str(c) for c in cmd)

            # Block osascript calls that open System Preferences
            if "osascript" in cmd_str and any(x in cmd_str for x in ["System Preferences", "System Settings", "Security & Privacy"]):
                # Return a mock response
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
                return mock_result

            # Block any command that tries to open System Preferences directly
            if any(
                x in cmd_str for x in ["open -b com.apple.preference", "open /System/Library/PreferencePanes", "x-apple.systempreferences"]
            ):
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                mock_result.stderr = ""
                return mock_result

            # For test_permissions.py, let it use its own mocks
            import inspect

            frame = inspect.currentframe()
            while frame:
                filename = frame.f_code.co_filename
                if "test_permissions.py" in filename:
                    # Let the test use its own mock
                    return original_subprocess_run(cmd, *args, **kwargs)
                frame = frame.f_back

        # For other safe commands, allow them through
        if isinstance(cmd, list) and len(cmd) > 0:
            safe_commands = ["which", "uname", "sw_vers", "id", "groups"]
            if cmd[0] in safe_commands:
                return original_subprocess_run(cmd, *args, **kwargs)

        # Default: return empty result for safety
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)


@pytest.fixture(scope="session")
def qapp_session():
    """Create a QApplication that lasts for the entire test session."""
    # Only import when needed
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
    yield app
    # Don't quit - let pytest handle cleanup
