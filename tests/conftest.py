"""Pytest configuration and shared fixtures."""
import os
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


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
def mock_platform(monkeypatch: pytest.MonkeyPatch) -> Generator[Mock, None, None]:
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
