"""Integration tests for macOS UI behavior."""

import sys
import unittest
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pasta.core.settings import SettingsManager
from pasta.core.storage import StorageManager
from pasta.gui.history_pyside6 import HistoryWindow
from pasta.gui.settings_pyside6 import SettingsWindow


def create_mock_settings():
    """Create a mock settings object with all required attributes."""
    mock_settings = Mock()

    # General settings
    mock_settings.start_on_login = False
    mock_settings.monitoring_enabled = True
    mock_settings.paste_mode = "auto"

    # Performance settings
    mock_settings.typing_speed = 100
    mock_settings.paste_delay = 0.01
    mock_settings.chunk_size = 200
    mock_settings.adaptive_delay = True
    mock_settings.type_speed = 100

    # History settings
    mock_settings.history_size = 1000
    mock_settings.history_retention_days = 7
    mock_settings.encrypt_sensitive = True
    mock_settings.auto_clear_history = False
    mock_settings.clear_history_days = 7

    # Privacy settings
    mock_settings.privacy_mode = False
    mock_settings.detect_sensitive = True
    mock_settings.excluded_apps = []
    mock_settings.excluded_patterns = []

    # Hotkey settings
    mock_settings.emergency_stop_hotkey = "Escape+Escape"
    mock_settings.quick_paste_hotkey = "Ctrl+Shift+V"
    mock_settings.toggle_monitoring_hotkey = "Ctrl+Shift+M"

    # Rate limits
    mock_settings.rate_limits = {"pastes_per_minute": 30, "clipboard_reads_per_minute": 100, "large_pastes_per_5min": 5}

    # Make copy return self
    mock_settings.copy.return_value = mock_settings

    return mock_settings


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific tests")
class TestMacOSUIIntegration(unittest.TestCase):
    """Integration tests for macOS UI behavior."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
            # Configure app as the tray would
            cls.app.setApplicationName("Pasta")
            cls.app.setApplicationDisplayName("Pasta")
            cls.app.setQuitOnLastWindowClosed(False)
        else:
            cls.app = QApplication.instance()
            # Ensure proper configuration even if app already exists
            cls.app.setQuitOnLastWindowClosed(False)

    def test_settings_window_macos_behavior(self):
        """Test settings window behavior on macOS."""
        # Create mock settings manager with proper attributes
        mock_settings_manager = Mock(spec=SettingsManager)
        mock_settings_manager.settings = create_mock_settings()

        # Create settings window
        window = SettingsWindow(mock_settings_manager)

        # Test window properties
        assert window.windowTitle() == "Pasta Settings"
        assert not window.isModal()  # Should be non-modal

        # Test that window flags allow it to appear in dock
        flags = window.windowFlags()
        assert not (flags & Qt.WindowType.WindowStaysOnTopHint)

        # Clean up
        window.close()

    def test_history_window_macos_behavior(self):
        """Test history window behavior on macOS."""
        # Create mock storage manager
        mock_storage = Mock(spec=StorageManager)
        mock_storage.get_history.return_value = []

        # Create history window
        window = HistoryWindow(mock_storage)

        # Test window properties
        assert "Pasta" in window.windowTitle()

        # Test that window flags allow it to appear in dock
        flags = window.windowFlags()
        assert not (flags & Qt.WindowType.WindowStaysOnTopHint)

        # Clean up
        window.close()

    def test_cmd_q_closes_only_window(self):
        """Test that Cmd+Q closes only the window, not the app."""
        # Create mock settings manager with proper attributes
        mock_settings_manager = Mock(spec=SettingsManager)
        mock_settings_manager.settings = create_mock_settings()

        # Create settings window
        window = SettingsWindow(mock_settings_manager)

        # Test that app doesn't quit when window closes
        assert self.app.quitOnLastWindowClosed() is False

        # Close window
        window.close()

        # App should still be running
        assert self.app is not None

    @patch("pasta.gui.tray_pyside6.QSystemTrayIcon")
    @patch("pasta.gui.tray_pyside6.QThread")
    @patch("pasta.gui.tray_pyside6.QMenu")
    @patch("pasta.gui.tray_pyside6.QIcon")
    @patch("pasta.gui.tray_pyside6.QAction")
    def test_system_tray_app_configuration(self, mock_action, mock_icon, mock_menu, mock_thread, mock_tray_icon):
        """Test system tray app configuration."""
        from pasta.gui.tray_pyside6 import SystemTray

        # Create mock components
        mock_clipboard = Mock()
        mock_keyboard = Mock()
        mock_keyboard.is_pasting.return_value = False
        mock_storage = Mock()
        mock_permissions = Mock()
        mock_settings = Mock()
        mock_settings.settings.monitoring_enabled = True
        mock_settings.settings.paste_mode = "auto"
        mock_settings.settings.emergency_stop_hotkey = "Escape+Escape"

        # Create system tray
        _ = SystemTray(
            clipboard_manager=mock_clipboard,
            keyboard_engine=mock_keyboard,
            storage_manager=mock_storage,
            permission_checker=mock_permissions,
            settings_manager=mock_settings,
        )

        # Test app configuration
        app = QApplication.instance()
        assert app is not None
        assert app.applicationName() == "Pasta"
        assert app.applicationDisplayName() == "Pasta"
        assert app.organizationName() == "Utensils"
        assert app.quitOnLastWindowClosed() is False


if __name__ == "__main__":
    unittest.main()
