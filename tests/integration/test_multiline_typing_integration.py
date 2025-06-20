"""Integration tests for multi-line typing functionality."""

from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray
from pasta.utils.permissions import PermissionChecker


class TestMultilineTypingIntegration:
    """Integration tests for multi-line typing with real components."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test.db")

    @pytest.fixture
    def components(self, temp_db):
        """Create real component instances."""
        return {
            "clipboard_manager": ClipboardManager(),
            "keyboard_engine": PastaKeyboardEngine(),
            "storage_manager": StorageManager(temp_db),
            "permission_checker": PermissionChecker(),
        }

    def test_multiline_paste_via_tray(self, components):
        """Test multi-line text paste through system tray."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            # Mock the keyboard engine's _ensure_pyautogui method to return our mock
            mock_pyautogui = Mock()
            components["keyboard_engine"]._ensure_pyautogui = Mock(return_value=mock_pyautogui)

            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set typing mode
            tray.enabled = True
            tray.set_paste_mode("typing")

            # Add multi-line content to storage
            multiline_entry = {
                "content": "First line of text\nSecond line of text\nThird line of text",
                "content_type": "text",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
            }
            components["storage_manager"].save_entry(multiline_entry)

            # Call paste_last_item
            tray.paste_last_item()

            # Verify pyautogui was called correctly
            assert mock_pyautogui.write.call_count == 3  # Three lines
            assert mock_pyautogui.press.call_count == 2  # Two line breaks

            # Check the actual calls
            write_calls = [call.args[0] for call in mock_pyautogui.write.call_args_list]
            assert "First line of text" in write_calls
            assert "Second line of text" in write_calls
            assert "Third line of text" in write_calls

    def test_code_block_paste(self, components):
        """Test pasting a code block with proper formatting."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            # Mock the keyboard engine's _ensure_pyautogui method to return our mock
            mock_pyautogui = Mock()
            components["keyboard_engine"]._ensure_pyautogui = Mock(return_value=mock_pyautogui)

            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set typing mode
            tray.enabled = True
            tray.set_paste_mode("typing")

            # Add code block to storage
            code_entry = {
                "content": """def greet(name):
    print(f"Hello, {name}!")
    return f"Greeted {name}"

# Use the function
result = greet("World")
print(result)""",
                "content_type": "text",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
            }
            components["storage_manager"].save_entry(code_entry)

            # Call paste_last_item
            tray.paste_last_item()

            # Verify proper number of line breaks
            lines = code_entry["content"].split("\n")
            expected_enters = len(lines) - 1
            assert mock_pyautogui.press.call_count == expected_enters

    def test_empty_lines_handling(self, components):
        """Test handling of empty lines in multi-line text."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            # Mock the keyboard engine's _ensure_pyautogui method to return our mock
            mock_pyautogui = Mock()
            components["keyboard_engine"]._ensure_pyautogui = Mock(return_value=mock_pyautogui)

            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set typing mode
            tray.enabled = True
            tray.set_paste_mode("typing")

            # Add text with empty lines
            entry_with_empty = {
                "content": "First paragraph\n\nSecond paragraph after empty line\n\n\nThird with multiple empty lines",
                "content_type": "text",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
            }
            components["storage_manager"].save_entry(entry_with_empty)

            # Call paste_last_item
            tray.paste_last_item()

            # Verify empty lines are handled
            lines = entry_with_empty["content"].split("\n")
            assert mock_pyautogui.press.call_count == len(lines) - 1

    def test_windows_line_endings(self, components):
        """Test handling of Windows-style line endings."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            # Mock the keyboard engine's _ensure_pyautogui method to return our mock
            mock_pyautogui = Mock()
            components["keyboard_engine"]._ensure_pyautogui = Mock(return_value=mock_pyautogui)

            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set typing mode
            tray.enabled = True
            tray.set_paste_mode("typing")

            # Add text with Windows line endings
            windows_entry = {
                "content": "Windows line 1\r\nWindows line 2\r\nWindows line 3",
                "content_type": "text",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
            }
            components["storage_manager"].save_entry(windows_entry)

            # Call paste_last_item
            tray.paste_last_item()

            # Should handle \r\n as single line break
            # The split on \n will handle \r\n correctly
            assert mock_pyautogui.write.call_count >= 3
