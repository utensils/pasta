"""Tests for window signals and events."""

import os
import sys
import unittest
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from pasta.core.settings import Settings, SettingsManager
from pasta.core.storage import StorageManager
from pasta.gui.history_pyside6 import HistoryWindow
from pasta.gui.settings_pyside6_improved import SettingsWindow


class TestWindowSignals(unittest.TestCase):
    """Test window signals are properly emitted."""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests."""
        if not QApplication.instance():
            cls.app = QApplication([])

    def test_settings_window_has_closed_signal(self):
        """Test that SettingsWindow has a 'closed' signal."""
        settings_manager = MagicMock(spec=SettingsManager)
        settings_manager.settings = Settings()

        window = SettingsWindow(settings_manager)

        # Check that closed signal exists
        self.assertTrue(hasattr(window, "closed"))
        self.assertIsInstance(window.closed, Signal)

    def test_history_window_has_closed_signal(self):
        """Test that HistoryWindow has a 'closed' signal."""
        storage_manager = MagicMock(spec=StorageManager)
        storage_manager.get_history.return_value = []

        window = HistoryWindow(storage_manager)

        # Check that closed signal exists
        self.assertTrue(hasattr(window, "closed"))
        self.assertIsInstance(window.closed, Signal)

    @pytest.mark.skipif(
        sys.platform != "darwin" and os.environ.get("CI") == "true", reason="Qt window tests require display or macOS environment"
    )
    def test_settings_window_emits_closed_signal(self):
        """Test that SettingsWindow emits 'closed' signal when closed."""
        settings_manager = MagicMock(spec=SettingsManager)
        settings_manager.settings = Settings()

        # Mock DockIconManager to prevent AppKit import
        from unittest.mock import patch

        with patch("pasta.gui.settings_pyside6_improved.DockIconManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            window = SettingsWindow(settings_manager)

            # Connect a mock slot to the signal
            mock_slot = MagicMock()
            window.closed.connect(mock_slot)

            # Close the window
            close_event = QCloseEvent()
            window.closeEvent(close_event)
            close_event.accept()

            # Verify signal was emitted
            mock_slot.assert_called_once()

    @pytest.mark.skipif(
        sys.platform != "darwin" and os.environ.get("CI") == "true", reason="Qt window tests require display or macOS environment"
    )
    def test_history_window_emits_closed_signal(self):
        """Test that HistoryWindow emits 'closed' signal when closed."""
        storage_manager = MagicMock(spec=StorageManager)
        storage_manager.get_history.return_value = []

        # Mock DockIconManager to prevent AppKit import
        from unittest.mock import patch

        with patch("pasta.gui.history_pyside6.DockIconManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            window = HistoryWindow(storage_manager)

            # Connect a mock slot to the signal
            mock_slot = MagicMock()
            window.closed.connect(mock_slot)

            # Close the window
            close_event = QCloseEvent()
            window.closeEvent(close_event)
            close_event.accept()

            # Verify signal was emitted
            mock_slot.assert_called_once()

    @pytest.mark.skipif(
        sys.platform != "darwin" and os.environ.get("CI") == "true", reason="Qt window tests require display or macOS environment"
    )
    def test_window_signals_can_be_connected(self):
        """Test that window closed signals can be connected to slots."""
        settings_manager = MagicMock(spec=SettingsManager)
        settings_manager.settings = Settings()
        storage_manager = MagicMock(spec=StorageManager)
        storage_manager.get_history.return_value = []

        # Mock DockIconManager
        from unittest.mock import patch

        with (
            patch("pasta.gui.settings_pyside6_improved.DockIconManager") as mock_settings_dm,
            patch("pasta.gui.history_pyside6.DockIconManager") as mock_history_dm,
        ):
            mock_settings_manager = MagicMock()
            mock_history_manager = MagicMock()
            mock_settings_dm.get_instance.return_value = mock_settings_manager
            mock_history_dm.get_instance.return_value = mock_history_manager

            # Create windows
            settings_window = SettingsWindow(settings_manager)
            history_window = HistoryWindow(storage_manager)

            # Create mock slots
            mock_settings_slot = MagicMock()
            mock_history_slot = MagicMock()

            # Connect signals - this should not raise AttributeError
            settings_window.closed.connect(mock_settings_slot)
            history_window.closed.connect(mock_history_slot)

            # Verify connections work by closing windows
            close_event = QCloseEvent()

            # Close settings window
            settings_window.closeEvent(close_event)
            if close_event.isAccepted():
                mock_settings_slot.assert_called_once()

            # Close history window
            history_window.closeEvent(close_event)
            if close_event.isAccepted():
                mock_history_slot.assert_called_once()


if __name__ == "__main__":
    unittest.main()
