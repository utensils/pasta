"""Tests for paste_last_item functionality."""

from unittest.mock import Mock, patch

import pytest

from pasta.gui.tray_pyside6 import SystemTray


class TestPasteLastItem:
    """Test paste_last_item method behavior."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "clipboard_manager": Mock(),
            "keyboard_engine": Mock(),
            "storage_manager": Mock(),
            "permission_checker": Mock(),
            "settings_manager": Mock(),
        }

    @pytest.fixture
    def tray(self, mock_components):
        """Create a SystemTray instance for testing."""
        # Mock the settings
        mock_components["settings_manager"].settings.monitoring_enabled = True
        mock_components["settings_manager"].settings.paste_mode = "auto"
        mock_components["settings_manager"].settings.emergency_stop_hotkey = "Escape+Escape"

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
            tray = SystemTray(**mock_components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()
            return tray

    def test_paste_last_item_single_line(self, tray, mock_components):
        """Test pasting single-line content."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return single-line entry
        test_entry = {
            "content": "Single line test content",
            "content_type": "text",
            "timestamp": "2024-01-01T12:00:00",
            "hash": "test_hash",
        }
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was called
        mock_components["keyboard_engine"].paste_text.assert_called_once_with("Single line test content", method="typing")

    def test_paste_last_item_multi_line(self, tray, mock_components):
        """Test pasting multi-line content."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return multi-line entry
        multi_line_content = """Lorem ipsum dolor sit amet
Consectetur adipiscing elit
Sed do eiusmod tempor"""

        test_entry = {"content": multi_line_content, "content_type": "multiline", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was called with multi-line content
        mock_components["keyboard_engine"].paste_text.assert_called_once_with(multi_line_content, method="typing")

    def test_paste_last_item_no_entries(self, tray, mock_components):
        """Test when there are no entries in storage."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return no entries
        mock_components["storage_manager"].get_entries.return_value = []

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was not called
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_paste_last_item_disabled(self, tray, mock_components):
        """Test when tray is disabled."""
        tray.enabled = False
        tray.set_paste_mode("typing")

        # Mock storage to return entry
        test_entry = {"content": "Test content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was not called
        mock_components["keyboard_engine"].paste_text.assert_not_called()
        # Verify we didn't even check storage
        mock_components["storage_manager"].get_entries.assert_not_called()

    def test_paste_last_item_non_text_content(self, tray, mock_components):
        """Test when content is not text type."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return non-text entry
        test_entry = {"content": b"binary data", "content_type": "image", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was not called
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_paste_last_item_empty_content(self, tray, mock_components):
        """Test when content is empty."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return entry with empty content
        test_entry = {"content": "", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was not called (empty content fails the check)
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_paste_last_item_exception_handling(self, tray, mock_components):
        """Test exception handling in paste_last_item."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Mock storage to return entry
        test_entry = {"content": "Test content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Make paste_text raise an exception
        mock_components["keyboard_engine"].paste_text.side_effect = Exception("Test error")

        # Call paste_last_item - should not raise
        tray.paste_last_item()

        # Verify paste was attempted
        mock_components["keyboard_engine"].paste_text.assert_called_once()

    def test_paste_last_item_with_special_characters(self, tray, mock_components):
        """Test pasting content with special characters."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        # Content with special characters
        special_content = """Line with émojis 🎉
Line with symbols: @#$%^&*()
Line with quotes: 'single' "double"
Line with dots... and colons: like this"""

        test_entry = {"content": special_content, "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Verify paste was called with the exact content
        mock_components["keyboard_engine"].paste_text.assert_called_once_with(special_content, method="typing")
