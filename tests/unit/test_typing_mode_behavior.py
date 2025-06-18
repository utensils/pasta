"""Tests for keyboard/typing mode paste behavior."""

from unittest.mock import Mock, patch

import pytest

from pasta.gui.tray_pyside6 import SystemTray


class TestTypingModeBehavior:
    """Test cases for keyboard/typing mode automatic paste behavior."""

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
            # Mock _update_menu and _update_tray_icon to avoid Qt widget creation
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()
            return tray

    def test_typing_mode_does_not_auto_paste(self, tray, mock_components):
        """Test that typing mode does not automatically paste on clipboard change."""
        # Set paste mode to typing
        tray.set_paste_mode("typing")

        # Enable the tray
        tray.enabled = True

        # Create test clipboard entry
        test_entry = {"content": "Test content for typing", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash", "type": "text"}

        # Trigger clipboard change
        tray._on_clipboard_change(test_entry)

        # Should save to storage
        mock_components["storage_manager"].save_entry.assert_called_once_with(test_entry)

        # Should NOT trigger automatic paste
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_clipboard_mode_does_not_auto_paste(self, tray, mock_components):
        """Test that clipboard mode does not automatically paste on clipboard change."""
        # Set paste mode to clipboard
        tray.set_paste_mode("clipboard")

        # Enable the tray
        tray.enabled = True

        # Create test clipboard entry
        test_entry = {"content": "Test content for clipboard", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash", "type": "text"}

        # Trigger clipboard change
        tray._on_clipboard_change(test_entry)

        # Should save to storage
        mock_components["storage_manager"].save_entry.assert_called_once_with(test_entry)

        # Should NOT trigger automatic paste
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_auto_mode_does_not_paste(self, tray, mock_components):
        """Test that auto mode does not automatically paste."""
        # Set paste mode to auto (default)
        tray.set_paste_mode("auto")

        # Enable the tray
        tray.enabled = True

        # Create test clipboard entry
        test_entry = {"content": "Test content", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash", "type": "text"}

        # Trigger clipboard change
        tray._on_clipboard_change(test_entry)

        # Should save to storage
        mock_components["storage_manager"].save_entry.assert_called_once_with(test_entry)

        # Should NOT trigger paste in auto mode
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_disabled_tray_does_not_paste_in_typing_mode(self, tray, mock_components):
        """Test that disabled tray does not paste even in typing mode."""
        # Set paste mode to typing
        tray.set_paste_mode("typing")

        # Disable the tray
        tray.enabled = False

        # Create test clipboard entry
        test_entry = {"content": "Test content", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash", "type": "text"}

        # Trigger clipboard change
        tray._on_clipboard_change(test_entry)

        # Should still save to storage
        mock_components["storage_manager"].save_entry.assert_called_once_with(test_entry)

        # Should NOT trigger paste when disabled
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_paste_last_item_error_handling(self, tray, mock_components):
        """Test error handling during paste_last_item operation."""
        # Set paste mode to typing
        tray.set_paste_mode("typing")
        tray.enabled = True

        # Mock storage to return an entry
        test_entry = {"content": "Test content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Mock paste to raise an exception
        mock_components["keyboard_engine"].paste_text.side_effect = Exception("Paste error")

        # Call paste_last_item - should not crash
        tray.paste_last_item()

        # Paste was attempted
        mock_components["keyboard_engine"].paste_text.assert_called_once_with("Test content", method="typing")

    def test_paste_last_item_with_typing_mode(self, tray, mock_components):
        """Test paste_last_item uses typing method when in typing mode."""
        # Set paste mode to typing
        tray.set_paste_mode("typing")
        tray.enabled = True

        # Mock storage to return an entry
        test_entry = {"content": "Test content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Should use typing method
        mock_components["keyboard_engine"].paste_text.assert_called_once_with("Test content", method="typing")

    def test_paste_last_item_with_clipboard_mode(self, tray, mock_components):
        """Test paste_last_item uses clipboard method when in clipboard mode."""
        tray.enabled = True
        tray.set_paste_mode("clipboard")

        # Mock storage to return an entry
        test_entry = {"content": "Test content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        # Call paste_last_item
        tray.paste_last_item()

        # Should use clipboard method
        mock_components["keyboard_engine"].paste_text.assert_called_once_with("Test content", method="clipboard")
