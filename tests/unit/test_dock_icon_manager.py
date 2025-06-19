"""Tests for macOS dock icon visibility management."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest


# Skip these tests in CI on non-macOS platforms to avoid AppKit import issues
@pytest.mark.skipif(
    (sys.platform != "darwin" and os.environ.get("CI") == "true") or os.environ.get("PASTA_TEST_SKIP_APPKIT") == "1",
    reason="DockIconManager tests require macOS or mocked environment without PASTA_TEST_SKIP_APPKIT",
)
class TestDockIconManager(unittest.TestCase):
    """Test dock icon visibility management on macOS."""

    def setUp(self):
        """Set up test dependencies."""
        # Create patcher for platform check
        self.platform_patcher = patch("sys.platform", "darwin")
        self.platform_patcher.start()

        # Reset singleton for each test
        from pasta.utils.dock_manager import DockIconManager

        DockIconManager._reset_singleton()

    def tearDown(self):
        """Clean up after tests."""
        self.platform_patcher.stop()

        # Clean up AppKit from sys.modules if it was mocked
        if "AppKit" in sys.modules and hasattr(sys.modules["AppKit"], "_mock_name"):
            del sys.modules["AppKit"]

        # Reset singleton after each test
        from pasta.utils.dock_manager import DockIconManager

        DockIconManager._reset_singleton()

    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_dock_icon_manager_creation(self, mock_appkit):
        """Test DockIconManager can be created on macOS."""
        from pasta.utils.dock_manager import DockIconManager

        manager = DockIconManager()
        manager._appkit_available = True  # Force availability for test
        self.assertIsNotNone(manager)
        self.assertFalse(manager.is_visible())

    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_show_dock_icon(self, mock_appkit):
        """Test showing dock icon."""
        # Put mock in sys.modules
        sys.modules["AppKit"] = mock_appkit

        from pasta.utils.dock_manager import DockIconManager

        # Mock NSApp and NSBundle
        mock_app = MagicMock()
        mock_bundle = MagicMock()
        mock_info_dict = {}

        mock_appkit.NSApp = mock_app
        mock_appkit.NSBundle.mainBundle.return_value = mock_bundle
        mock_bundle.infoDictionary.return_value = mock_info_dict
        mock_appkit.NSApplicationActivationPolicyRegular = 0

        manager = DockIconManager()
        manager._appkit_available = True  # Force availability for test
        manager.show()

        # Verify LSUIElement was set to False (show in dock)
        self.assertEqual(mock_info_dict.get("LSUIElement"), "0")
        self.assertTrue(manager.is_visible())

    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_hide_dock_icon(self, mock_appkit):
        """Test hiding dock icon."""
        # Put mock in sys.modules
        sys.modules["AppKit"] = mock_appkit

        from pasta.utils.dock_manager import DockIconManager

        # Mock NSApp and NSBundle
        mock_app = MagicMock()
        mock_bundle = MagicMock()
        mock_info_dict = {}

        mock_appkit.NSApp = mock_app
        mock_appkit.NSBundle.mainBundle.return_value = mock_bundle
        mock_bundle.infoDictionary.return_value = mock_info_dict
        mock_appkit.NSApplicationActivationPolicyRegular = 0
        mock_appkit.NSApplicationActivationPolicyAccessory = 1

        manager = DockIconManager()
        # Force appkit to be available since we're mocking it
        manager._appkit_available = True

        manager.show()  # First show it
        self.assertEqual(mock_info_dict.get("LSUIElement"), "0")

        manager.hide()

        # Verify LSUIElement was set to True (hide from dock)
        self.assertEqual(mock_info_dict.get("LSUIElement"), "1")
        self.assertFalse(manager.is_visible())

    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_reference_counting(self, mock_appkit):
        """Test reference counting for multiple windows."""
        # Put mock in sys.modules
        sys.modules["AppKit"] = mock_appkit

        from pasta.utils.dock_manager import DockIconManager

        # Mock NSApp and NSBundle
        mock_app = MagicMock()
        mock_bundle = MagicMock()
        mock_info_dict = {}

        mock_appkit.NSApp = mock_app
        mock_appkit.NSBundle.mainBundle.return_value = mock_bundle
        mock_bundle.infoDictionary.return_value = mock_info_dict
        mock_appkit.NSApplicationActivationPolicyRegular = 0
        mock_appkit.NSApplicationActivationPolicyAccessory = 1

        manager = DockIconManager()
        manager._appkit_available = True  # Force availability for test

        # Add two references (e.g., settings and history windows)
        manager.add_reference("settings")
        self.assertTrue(manager.is_visible())

        manager.add_reference("history")
        self.assertTrue(manager.is_visible())

        # Remove one reference - should still be visible
        manager.remove_reference("settings")
        self.assertTrue(manager.is_visible())

        # Remove last reference - should hide
        manager.remove_reference("history")
        self.assertFalse(manager.is_visible())

    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_duplicate_references_ignored(self, mock_appkit):
        """Test that duplicate references are handled correctly."""
        from pasta.utils.dock_manager import DockIconManager

        # Mock setup
        mock_appkit.NSBundle.mainBundle.return_value.infoDictionary.return_value = {}

        manager = DockIconManager()
        manager._appkit_available = True  # Force availability for test

        # Add same reference twice
        manager.add_reference("settings")
        manager.add_reference("settings")

        # Should only need to remove once
        manager.remove_reference("settings")
        self.assertFalse(manager.is_visible())

    def test_non_macos_platform(self):
        """Test that DockIconManager is no-op on non-macOS platforms."""
        # Temporarily change platform
        with patch("sys.platform", "linux"):
            from pasta.utils.dock_manager import DockIconManager

            manager = DockIconManager()

            # All operations should be no-ops
            manager.show()
            self.assertFalse(manager.is_visible())

            manager.add_reference("test")
            self.assertFalse(manager.is_visible())

    @pytest.mark.skipif(os.environ.get("PASTA_TEST_SKIP_APPKIT") == "1", reason="Skip when dock manager is mocked")
    def test_appkit_not_available(self):
        """Test behavior when AppKit is not available."""
        from pasta.utils.dock_manager import DockIconManager

        # Create manager and force AppKit to be unavailable
        manager = DockIconManager()
        manager._appkit_available = False

        # All operations should be no-ops
        manager.show()
        self.assertFalse(manager.is_visible())

        manager.add_reference("test")
        self.assertFalse(manager.is_visible())

        manager.hide()
        self.assertFalse(manager.is_visible())


@pytest.mark.skipif(
    sys.platform != "darwin" and os.environ.get("CI") == "true", reason="DockIconManager tests require macOS or mocked environment"
)
class TestDockIconIntegration(unittest.TestCase):
    """Test dock icon integration with windows."""

    @pytest.mark.skipif(
        os.environ.get("PASTA_TEST_SKIP_APPKIT") == "1", reason="Skip AppKit tests in Nix environment to avoid Qt conflicts"
    )
    @patch("sys.platform", "darwin")
    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_settings_window_shows_dock_icon(self, mock_appkit):
        """Test that opening settings window shows dock icon."""
        from PySide6.QtWidgets import QApplication

        from pasta.gui.settings_pyside6_improved import SettingsWindow

        # Set up mocks
        mock_appkit.NSBundle.mainBundle.return_value.infoDictionary.return_value = {}

        # Create app if needed
        if not QApplication.instance():
            QApplication([])

        # Create settings window
        # Create a proper settings mock
        from pasta.core.settings import Settings

        settings_manager = MagicMock()
        settings_manager.settings = Settings()
        settings_manager.settings.paste_mode = MagicMock()
        settings_manager.settings.paste_mode.value = "auto"

        with patch("pasta.gui.settings_pyside6_improved.DockIconManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            window = SettingsWindow(settings_manager)
            window.show()

            # Verify dock icon was shown
            mock_manager.add_reference.assert_called_once_with("settings")

    @pytest.mark.skipif(
        os.environ.get("PASTA_TEST_SKIP_APPKIT") == "1", reason="Skip AppKit tests in Nix environment to avoid Qt conflicts"
    )
    @patch("sys.platform", "darwin")
    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_history_window_shows_dock_icon(self, mock_appkit):
        """Test that opening history window shows dock icon."""
        from PySide6.QtWidgets import QApplication

        from pasta.core.storage import StorageManager
        from pasta.gui.history_pyside6 import HistoryWindow

        # Set up mocks
        mock_appkit.NSBundle.mainBundle.return_value.infoDictionary.return_value = {}

        # Create app if needed
        if not QApplication.instance():
            QApplication([])

        # Create history window
        storage_manager = MagicMock(spec=StorageManager)
        storage_manager.get_history.return_value = []

        with patch("pasta.gui.history_pyside6.DockIconManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            window = HistoryWindow(storage_manager)
            window.show()

            # Verify dock icon was shown
            mock_manager.add_reference.assert_called_once_with("history")

    @pytest.mark.skipif(
        os.environ.get("PASTA_TEST_SKIP_APPKIT") == "1", reason="Skip AppKit tests in Nix environment to avoid Qt conflicts"
    )
    @patch("sys.platform", "darwin")
    @patch("pasta.utils.dock_manager.AppKit", create=True)
    def test_closing_window_hides_dock_icon(self, mock_appkit):
        """Test that closing windows hides dock icon when no windows remain."""
        from PySide6.QtGui import QCloseEvent
        from PySide6.QtWidgets import QApplication

        from pasta.gui.settings_pyside6_improved import SettingsWindow

        # Set up mocks
        mock_appkit.NSBundle.mainBundle.return_value.infoDictionary.return_value = {}

        # Create app if needed
        if not QApplication.instance():
            QApplication([])

        # Create a proper settings mock
        from pasta.core.settings import Settings

        settings_manager = MagicMock()
        settings_manager.settings = Settings()
        settings_manager.settings.paste_mode = MagicMock()
        settings_manager.settings.paste_mode.value = "auto"

        with patch("pasta.gui.settings_pyside6_improved.DockIconManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            window = SettingsWindow(settings_manager)
            window.show()

            # Close the window
            close_event = QCloseEvent()
            window.closeEvent(close_event)
            close_event.accept()

            # Verify dock icon reference was removed
            mock_manager.remove_reference.assert_called_once_with("settings")


if __name__ == "__main__":
    unittest.main()
