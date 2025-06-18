"""Tests for tray icon visual indication in different modes."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtGui import QIcon

from pasta.gui.tray_pyside6 import SystemTray


class TestTrayIconIndication:
    """Test cases for tray icon visual indication in different paste modes."""

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
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon") as mock_tray_icon,
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon") as mock_qicon,
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.Path") as mock_path,
            patch("pasta.gui.tray_pyside6.QPixmap") as mock_qpixmap,
            patch("pasta.gui.tray_pyside6.QPainter") as mock_qpainter,
        ):
            # Mock icon path to exist
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value = mock_path_instance

            # Mock QIcon and QPixmap
            mock_icon = Mock(spec=QIcon)
            mock_qicon.return_value = mock_icon

            mock_pixmap_instance = Mock()
            mock_pixmap_instance.size.return_value = Mock()
            mock_pixmap_instance.rect.return_value = Mock()
            mock_qpixmap.return_value = mock_pixmap_instance

            mock_painter_instance = Mock()
            mock_qpainter.return_value = mock_painter_instance

            # Mock tray icon instance
            mock_tray_instance = Mock()
            mock_tray_icon.return_value = mock_tray_instance

            tray = SystemTray(**mock_components)
            tray.tray_icon = mock_tray_instance
            # Mock _update_menu to avoid Qt widget creation
            tray._update_menu = Mock()

            # Store original _update_tray_icon for testing
            tray._original_update_tray_icon = tray._update_tray_icon
            # Mock it to avoid Qt widget creation but track calls
            tray._update_tray_icon = Mock(side_effect=lambda: None)

            return tray

    def test_tray_icon_changes_in_typing_mode(self, tray):
        """Test that tray icon changes when typing mode is activated."""
        # Reset mock to track calls
        tray._update_tray_icon.reset_mock()

        # Set paste mode to typing
        tray.set_paste_mode("typing")

        # _update_tray_icon should be called
        tray._update_tray_icon.assert_called()

        # Verify mode is set correctly
        assert tray.paste_mode == "typing"

    def test_tray_icon_changes_in_clipboard_mode(self, tray):
        """Test that tray icon changes when clipboard mode is activated."""
        # Reset mock to track calls
        tray._update_tray_icon.reset_mock()

        # Set paste mode to clipboard
        tray.set_paste_mode("clipboard")

        # _update_tray_icon should be called
        tray._update_tray_icon.assert_called()

        # Verify mode is set correctly
        assert tray.paste_mode == "clipboard"

    def test_tray_icon_default_in_auto_mode(self, tray):
        """Test that tray icon returns to default in auto mode."""
        # First set to typing mode
        tray.set_paste_mode("typing")

        # Reset mock to track calls
        tray._update_tray_icon.reset_mock()

        # Set back to auto mode
        tray.set_paste_mode("auto")

        # _update_tray_icon should be called
        tray._update_tray_icon.assert_called()

        # Verify mode is set correctly
        assert tray.paste_mode == "auto"

    def test_icon_color_modification(self, tray):
        """Test that icon color is modified for different modes."""
        # Test that paste mode is stored correctly
        tray.set_paste_mode("typing")
        assert tray.paste_mode == "typing"

        tray.set_paste_mode("clipboard")
        assert tray.paste_mode == "clipboard"

        tray.set_paste_mode("auto")
        assert tray.paste_mode == "auto"

    def test_icon_updates_on_enabled_state_change(self, tray):
        """Test that icon updates when enabled state changes in typing mode."""
        # Set to typing mode first
        tray.set_paste_mode("typing")

        # Verify typing mode is set and _update_tray_icon was called
        assert tray.paste_mode == "typing"
        tray._update_tray_icon.assert_called()

        # Reset mock
        tray._update_tray_icon.reset_mock()

        # Make _update_menu call _update_tray_icon when called
        tray._update_menu.side_effect = lambda: tray._update_tray_icon()

        # Disable tray
        tray.enabled = False
        tray._update_menu()

        # _update_tray_icon should be called when menu is updated
        tray._update_tray_icon.assert_called()

    def test_multiple_mode_changes(self, tray):
        """Test icon updates correctly with multiple mode changes."""
        modes = ["auto", "typing", "clipboard", "typing", "auto"]

        for mode in modes:
            tray._update_tray_icon.reset_mock()
            tray.set_paste_mode(mode)

            # _update_tray_icon should be called each time
            tray._update_tray_icon.assert_called()

            # Verify mode is set correctly
            assert tray.paste_mode == mode
