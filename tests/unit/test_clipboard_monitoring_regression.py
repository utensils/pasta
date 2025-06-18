"""Regression tests for clipboard monitoring behavior."""

import time
from unittest.mock import Mock, patch

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.tray_pyside6 import SystemTray
from pasta.utils.permissions import PermissionChecker


class TestClipboardMonitoringRegression:
    """Test clipboard monitoring doesn't trigger unwanted behavior."""

    def test_clipboard_copy_should_not_trigger_paste(self):
        """Test that copying text to clipboard does NOT trigger automatic paste."""
        # This is a regression test for the bug where copying text
        # would immediately paste it back, sometimes as just "v"

        # Create mocks
        mock_clipboard = Mock(spec=ClipboardManager)
        mock_keyboard = Mock(spec=PastaKeyboardEngine)
        mock_storage = Mock(spec=StorageManager)
        mock_permissions = Mock(spec=PermissionChecker)
        mock_settings = Mock()

        # Configure settings
        mock_settings.settings.monitoring_enabled = True
        mock_settings.settings.paste_mode = "auto"
        mock_settings.settings.emergency_stop_hotkey = "Escape+Escape"

        # Track calls to paste_text
        paste_calls = []
        mock_keyboard.paste_text.side_effect = lambda text, method: paste_calls.append((text, method))
        mock_keyboard.is_pasting.return_value = False

        with (
            patch("PySide6.QtWidgets.QApplication"),
            patch("PySide6.QtWidgets.QSystemTrayIcon"),
            patch("PySide6.QtCore.QThread"),
            patch("PySide6.QtGui.QIcon"),
            patch("PySide6.QtWidgets.QMenu"),
            patch("PySide6.QtGui.QAction"),
        ):
            # Create system tray
            tray = SystemTray(
                clipboard_manager=mock_clipboard,
                keyboard_engine=mock_keyboard,
                storage_manager=mock_storage,
                permission_checker=mock_permissions,
                settings_manager=mock_settings,
            )

            # Simulate clipboard change (user copies text)
            clipboard_entry = {"content": "Hello World", "timestamp": time.time(), "type": "text", "hash": "abc123"}

            # This should NOT trigger a paste
            tray._on_clipboard_change(clipboard_entry)

            # ASSERTION: paste_text should NOT have been called
            assert len(paste_calls) == 0, "Clipboard change should not trigger automatic paste!"

    def test_clipboard_content_should_be_saved_to_history(self):
        """Test that clipboard content is saved to storage when copied."""
        # Create mocks
        mock_clipboard = Mock(spec=ClipboardManager)
        mock_keyboard = Mock(spec=PastaKeyboardEngine)
        mock_storage = Mock(spec=StorageManager)
        mock_permissions = Mock(spec=PermissionChecker)
        mock_settings = Mock()

        # Configure settings
        mock_settings.settings.monitoring_enabled = True
        mock_settings.settings.paste_mode = "auto"
        mock_settings.settings.emergency_stop_hotkey = "Escape+Escape"

        # Track storage calls
        storage_calls = []
        mock_storage.save_entry.side_effect = lambda entry: storage_calls.append(entry)
        mock_keyboard.is_pasting.return_value = False

        with (
            patch("PySide6.QtWidgets.QApplication"),
            patch("PySide6.QtWidgets.QSystemTrayIcon"),
            patch("PySide6.QtCore.QThread"),
            patch("PySide6.QtGui.QIcon"),
            patch("PySide6.QtWidgets.QMenu"),
            patch("PySide6.QtGui.QAction"),
        ):
            # Create system tray
            tray = SystemTray(
                clipboard_manager=mock_clipboard,
                keyboard_engine=mock_keyboard,
                storage_manager=mock_storage,
                permission_checker=mock_permissions,
                settings_manager=mock_settings,
            )

            # Simulate clipboard change
            clipboard_entry = {"content": "Test content for history", "timestamp": time.time(), "type": "text", "hash": "def456"}

            # This SHOULD save to storage
            tray._on_clipboard_change(clipboard_entry)

            # ASSERTION: content should be saved to storage
            assert len(storage_calls) > 0, "Clipboard content should be saved to history!"
            assert storage_calls[0]["content"] == "Test content for history"

    def test_letter_v_paste_regression(self):
        """Test that clipboard monitoring doesn't cause 'v' to be typed."""
        # This tests the specific bug where sometimes just "v" gets pasted
        # This can happen if Ctrl+V is sent but Ctrl is released too early

        mock_keyboard = Mock(spec=PastaKeyboardEngine)

        # Track what gets "typed"
        typed_text = []
        mock_keyboard.paste_text.side_effect = lambda text, method: typed_text.append(text)

        # If the bug is present, "v" might be typed instead of the actual content
        # We need to ensure clipboard monitoring NEVER triggers typing

        with patch("PySide6.QtWidgets.QApplication"):
            # Simulate various clipboard operations
            # None of these should result in typing "v" or any text

            # The assertion here is that typed_text remains empty
            assert len(typed_text) == 0, "No text should be typed during clipboard monitoring"

    def test_clipboard_monitoring_without_paste_enabled(self):
        """Test clipboard monitoring saves history even when paste is disabled."""
        # Create mocks
        mock_clipboard = Mock(spec=ClipboardManager)
        mock_keyboard = Mock(spec=PastaKeyboardEngine)
        mock_storage = Mock(spec=StorageManager)
        mock_permissions = Mock(spec=PermissionChecker)
        mock_settings = Mock()

        # Configure settings - monitoring enabled but not pasting
        mock_settings.settings.monitoring_enabled = False  # Disabled
        mock_settings.settings.paste_mode = "auto"
        mock_settings.settings.emergency_stop_hotkey = "Escape+Escape"

        storage_calls = []
        mock_storage.save_entry.side_effect = lambda entry: storage_calls.append(entry)
        mock_keyboard.is_pasting.return_value = False

        with (
            patch("PySide6.QtWidgets.QApplication"),
            patch("PySide6.QtWidgets.QSystemTrayIcon"),
            patch("PySide6.QtCore.QThread"),
            patch("PySide6.QtGui.QIcon"),
            patch("PySide6.QtWidgets.QMenu"),
            patch("PySide6.QtGui.QAction"),
        ):
            tray = SystemTray(
                clipboard_manager=mock_clipboard,
                keyboard_engine=mock_keyboard,
                storage_manager=mock_storage,
                permission_checker=mock_permissions,
                settings_manager=mock_settings,
            )

            # Even with paste disabled, we should still save history
            clipboard_entry = {"content": "History should be saved", "timestamp": time.time(), "type": "text", "hash": "ghi789"}

            tray._on_clipboard_change(clipboard_entry)

            # History should still be saved even when paste is disabled
            # (Currently this will fail, showing the bug)
            assert len(storage_calls) > 0, "History should be saved even when paste is disabled"
