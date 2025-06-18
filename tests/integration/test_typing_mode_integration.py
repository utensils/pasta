"""Integration tests for typing mode feature."""

from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray
from pasta.utils.permissions import PermissionChecker


class TestTypingModeIntegration:
    """Integration tests for typing mode with real components."""

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

    def test_typing_mode_paste_behavior(self, components):
        """Test that typing mode does not auto-paste but paste_last_item works."""
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
            patch.object(components["keyboard_engine"], "paste_text") as mock_paste,
        ):
            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set typing mode
            tray.enabled = True
            tray.set_paste_mode("typing")

            # Simulate clipboard change
            test_entry = {
                "content": "Test typing mode",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
                "type": "text",
                "content_type": "text",  # Include both for compatibility
            }

            tray._on_clipboard_change(test_entry)

            # Should NOT auto-paste
            mock_paste.assert_not_called()

            # Verify entry was saved to storage
            entries = components["storage_manager"].get_entries()
            assert len(entries) > 0
            assert entries[0]["content"] == "Test typing mode"

            # Now test paste_last_item
            tray.paste_last_item()

            # Should paste with typing method
            mock_paste.assert_called_once_with("Test typing mode", method="typing")

    def test_clipboard_mode_paste_behavior(self, components):
        """Test that clipboard mode does not auto-paste but paste_last_item works."""
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
            patch.object(components["keyboard_engine"], "paste_text") as mock_paste,
        ):
            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray and set clipboard mode
            tray.enabled = True
            tray.set_paste_mode("clipboard")

            # Simulate clipboard change
            test_entry = {
                "content": "Test clipboard mode",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
                "type": "text",
                "content_type": "text",
            }

            tray._on_clipboard_change(test_entry)

            # Should NOT auto-paste
            mock_paste.assert_not_called()

            # Now test paste_last_item
            tray.paste_last_item()

            # Should paste with clipboard method
            mock_paste.assert_called_once_with("Test clipboard mode", method="clipboard")

    def test_auto_mode_no_paste(self, components):
        """Test that auto mode does not automatically paste."""
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
            patch.object(components["keyboard_engine"], "paste_text") as mock_paste,
        ):
            tray = SystemTray(**components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()

            # Enable tray with default auto mode
            tray.enabled = True
            assert tray.paste_mode == "auto"

            # Simulate clipboard change
            test_entry = {
                "content": "Test auto mode",
                "timestamp": "2024-01-01T12:00:00",
                "hash": "test_hash",
                "type": "text",
                "content_type": "text",
            }

            tray._on_clipboard_change(test_entry)

            # Verify no paste was triggered
            mock_paste.assert_not_called()

            # But entry should still be saved
            entries = components["storage_manager"].get_entries()
            assert len(entries) > 0
            assert entries[0]["content"] == "Test auto mode"
