"""Integration tests for macOS keyboard shortcuts in dialogs."""

import sys
import unittest
from unittest.mock import Mock

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
    mock_settings.typing_speed = 100
    mock_settings.paste_delay = 0.01
    mock_settings.chunk_size = 200
    mock_settings.adaptive_delay = True
    mock_settings.type_speed = 100
    mock_settings.history_size = 1000
    mock_settings.history_retention_days = 7
    mock_settings.encrypt_sensitive = True
    mock_settings.auto_clear_history = False
    mock_settings.clear_history_days = 7
    mock_settings.privacy_mode = False
    mock_settings.detect_sensitive = True
    mock_settings.excluded_apps = []
    mock_settings.excluded_patterns = []
    mock_settings.emergency_stop_hotkey = "Escape+Escape"
    mock_settings.quick_paste_hotkey = "Ctrl+Shift+V"
    mock_settings.toggle_monitoring_hotkey = "Ctrl+Shift+M"
    mock_settings.rate_limits = {"pastes_per_minute": 30, "clipboard_reads_per_minute": 100, "large_pastes_per_5min": 5}
    mock_settings.copy.return_value = mock_settings

    return mock_settings


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific tests")
class TestMacOSShortcuts(unittest.TestCase):
    """Test macOS keyboard shortcuts in dialog windows."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])
            cls.app.setQuitOnLastWindowClosed(False)
        else:
            cls.app = QApplication.instance()

    def test_settings_window_shortcuts(self):
        """Test that settings window has proper shortcuts."""
        # Create mock settings manager
        mock_settings_manager = Mock(spec=SettingsManager)
        mock_settings_manager.settings = create_mock_settings()

        # Create settings window
        window = SettingsWindow(mock_settings_manager)

        # Check that shortcuts exist (can't easily test actual behavior in unit tests)
        # But we can verify the window properties
        assert window.windowTitle() == "Pasta Settings"
        assert not window.isModal()

        # Verify window type allows native controls
        flags = window.windowFlags()
        # Should not have WindowStaysOnTopHint
        assert not (flags & Qt.WindowType.WindowStaysOnTopHint)

        window.close()

    def test_history_window_shortcuts(self):
        """Test that history window has proper shortcuts."""
        # Create mock storage manager
        mock_storage = Mock(spec=StorageManager)
        mock_storage.get_history.return_value = []

        # Create history window
        window = HistoryWindow(mock_storage)

        # Check window properties
        assert "Pasta" in window.windowTitle()

        # Verify it's a QMainWindow (has native controls)
        assert hasattr(window, "setCentralWidget")

        # Verify window type allows native controls
        flags = window.windowFlags()
        assert not (flags & Qt.WindowType.WindowStaysOnTopHint)

        window.close()

    def test_window_close_behavior(self):
        """Test that closing windows doesn't quit the app."""
        # Create and close a settings window
        mock_settings_manager = Mock(spec=SettingsManager)
        mock_settings_manager.settings = create_mock_settings()

        window = SettingsWindow(mock_settings_manager)
        # Don't actually show the window - just verify properties
        # window.show()  # REMOVED: This opens a real window

        # Verify app configuration without showing window
        assert self.app is not None
        assert self.app.quitOnLastWindowClosed() is False

        # Clean up
        window.close()


if __name__ == "__main__":
    unittest.main()
