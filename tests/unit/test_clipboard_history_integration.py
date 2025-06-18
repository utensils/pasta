"""Integration tests for clipboard history saving."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.storage import StorageManager
from pasta.gui.tray_pyside6 import ClipboardWorker, SystemTray


class TestClipboardHistoryIntegration:
    """Test that clipboard changes are properly saved to history."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database file."""
        return str(tmp_path / "test_history.db")

    def test_clipboard_entry_format_matches_storage_requirements(self):
        """Test that ClipboardManager creates entries with correct format for StorageManager."""
        # Create clipboard manager
        clipboard_manager = ClipboardManager()

        # Mock pyperclip to return test content
        with patch("pyperclip.paste", return_value="Test content"):
            # Manually trigger one monitoring iteration
            clipboard_manager._monitor_iteration()

            # Check the last entry in history
            assert len(clipboard_manager.history) > 0
            entry = clipboard_manager.history[-1]

            # Verify all required fields are present
            assert "content" in entry
            assert "timestamp" in entry
            assert "hash" in entry
            assert "content_type" in entry  # This was the bug - it was "type" before

            # Verify timestamp is in ISO format (string)
            assert isinstance(entry["timestamp"], str)
            # Should be parseable as ISO format
            datetime.fromisoformat(entry["timestamp"])

    def test_clipboard_to_storage_integration(self, temp_db):
        """Test that clipboard changes are saved to storage."""
        # Create components
        clipboard_manager = ClipboardManager()
        storage_manager = StorageManager(temp_db)

        # Track storage saves
        saved_entries = []
        original_save = storage_manager.save_entry

        def mock_save(entry):
            saved_entries.append(entry)
            return original_save(entry)

        storage_manager.save_entry = mock_save

        # Connect clipboard to storage (simulating what SystemTray does)
        clipboard_manager.register_callback(lambda entry: storage_manager.save_entry(entry))

        # Mock clipboard content
        with patch("pyperclip.paste", return_value="Test clipboard content"):
            # Trigger monitoring
            clipboard_manager._monitor_iteration()

            # Verify entry was saved
            assert len(saved_entries) == 1
            saved_entry = saved_entries[0]
            assert saved_entry["content"] == "Test clipboard content"
            assert saved_entry["content_type"] == "text"

        # Verify it's in the database
        entries = storage_manager.get_entries()
        assert len(entries) > 0
        assert entries[0]["content"] == "Test clipboard content"

    def test_clipboard_worker_emits_correct_format(self):
        """Test that ClipboardWorker emits entries in correct format."""
        clipboard_manager = ClipboardManager()
        worker = ClipboardWorker(clipboard_manager)

        # Track emitted signals
        emitted_entries = []
        worker.clipboard_changed.connect(lambda entry: emitted_entries.append(entry))

        # Create a test entry with correct format
        test_entry = {
            "content": "Test content",
            "timestamp": datetime.now().isoformat(),
            "hash": "test_hash",
            "content_type": "text",
        }

        # Trigger the callback
        worker._on_clipboard_change(test_entry)

        # Verify the emitted entry has correct format
        assert len(emitted_entries) == 1
        assert emitted_entries[0] == test_entry

    def test_system_tray_saves_clipboard_to_storage(self, temp_db):
        """Test that SystemTray properly saves clipboard changes to storage."""
        # Create mocks
        mock_clipboard = Mock(spec=ClipboardManager)
        mock_keyboard = Mock()
        mock_keyboard.is_pasting.return_value = False
        storage_manager = StorageManager(temp_db)
        mock_permissions = Mock()
        mock_settings = Mock()
        mock_settings.settings.monitoring_enabled = True
        mock_settings.settings.paste_mode = "auto"

        # Track what gets saved
        saved_entries = []
        original_save = storage_manager.save_entry

        def track_save(entry):
            saved_entries.append(entry)
            return original_save(entry)

        storage_manager.save_entry = track_save

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
                storage_manager=storage_manager,
                permission_checker=mock_permissions,
                settings_manager=mock_settings,
            )

            # Simulate clipboard change with correct format
            test_entry = {
                "content": "System tray test content",
                "timestamp": datetime.now().isoformat(),
                "hash": "test_hash_123",
                "content_type": "text",
            }

            # Call the clipboard change handler
            tray._on_clipboard_change(test_entry)

            # Verify it was saved
            assert len(saved_entries) == 1
            assert saved_entries[0]["content"] == "System tray test content"

        # Verify it's in the database
        entries = storage_manager.get_entries()
        assert len(entries) > 0
        assert entries[0]["content"] == "System tray test content"
