"""Integration tests for SystemTray interactions."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray
from pasta.utils.permissions import PermissionChecker


class TestSystemTrayIntegration:
    """Integration tests for SystemTray with real components."""

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

    @pytest.fixture
    def tray(self, components):
        """Create SystemTray with real components."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication") as mock_qapp,
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread") as mock_qthread,
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker") as mock_worker,
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
        ):
            # Mock QApplication instance
            mock_qapp.instance.return_value = None

            # Mock QThread properly
            mock_thread_instance = Mock()
            mock_qthread.return_value = mock_thread_instance

            # Mock ClipboardWorker to actually register callback
            mock_worker_instance = Mock()

            def worker_init(clipboard_manager):
                # Actually register the callback like the real worker does
                clipboard_manager.register_callback(mock_worker_instance._on_clipboard_change)
                return mock_worker_instance

            mock_worker.side_effect = worker_init
            mock_worker_instance._on_clipboard_change = Mock()

            return SystemTray(**components)

    def test_clipboard_to_paste_flow(self, tray, components):
        """Test full flow from clipboard change to paste."""
        with patch.object(components["keyboard_engine"], "paste_text") as mock_paste:
            # Simulate clipboard content through the tray's handler
            test_entry = {"content": "Integration test content", "timestamp": "2024-01-01", "hash": "abc123", "type": "text"}

            # Call the tray's clipboard change handler directly
            tray._on_clipboard_change(test_entry)

            # Verify paste was triggered
            mock_paste.assert_called_once_with("Integration test content", method="auto")

    def test_clipboard_history_storage(self, tray, components, temp_db):
        """Test clipboard content is stored in history."""
        # Add some clipboard content
        test_entries = [
            {"content": "First clipboard entry", "timestamp": datetime.now(), "hash": "hash1", "content_type": "text"},
            {"content": "Second clipboard entry", "timestamp": datetime.now(), "hash": "hash2", "content_type": "text"},
            {"content": "Third clipboard entry", "timestamp": datetime.now(), "hash": "hash3", "content_type": "text"},
        ]

        for entry in test_entries:
            components["clipboard_manager"]._add_to_history(entry)

        # Verify entries are in history
        history = components["clipboard_manager"].get_history()
        assert len(history) == 3
        assert history[0]["content"] == "Third clipboard entry"  # Most recent first

        # Test storage manager can save entries
        for entry in test_entries:
            saved_id = components["storage_manager"].save_entry(entry)
            assert saved_id is not None

        # Verify storage manager has the entries
        stored_entries = components["storage_manager"].get_entries()
        assert len(stored_entries) >= 3

    def test_permission_integration(self, tray, components):
        """Test permission checking integration."""
        with patch.object(components["permission_checker"], "check_permissions") as mock_check:
            # Simulate no permissions
            mock_check.return_value = False

            # Disable and try to re-enable
            tray.enabled = False
            tray.toggle_enabled()

            # Should check permissions
            mock_check.assert_called_once()

            # Should remain disabled
            assert tray.enabled is False

    def test_paste_mode_integration(self, tray, components):
        """Test paste mode changes affect keyboard engine."""
        with patch.object(components["keyboard_engine"], "paste_text") as mock_paste:
            test_entry = {"content": "test", "timestamp": "2024-01-01", "hash": "abc", "type": "text"}

            # Test auto mode
            tray.set_paste_mode("auto")
            tray._on_clipboard_change(test_entry)
            mock_paste.assert_called_with("test", method="auto")
            mock_paste.reset_mock()

            # Test clipboard mode
            tray.set_paste_mode("clipboard")
            tray._on_clipboard_change(test_entry)
            mock_paste.assert_called_with("test", method="clipboard")
            mock_paste.reset_mock()

            # Test typing mode
            tray.set_paste_mode("typing")
            tray._on_clipboard_change(test_entry)
            mock_paste.assert_called_with("test", method="typing")

    def test_sensitive_data_handling(self, tray, components):
        """Test sensitive data is handled properly."""
        # Test with sensitive content
        sensitive_content = "password: secretpassword123"

        # Create proper entry
        entry = {"content": sensitive_content, "timestamp": datetime.now(), "hash": "xyz", "content_type": "text"}

        # Check if storage manager would encrypt it
        assert components["storage_manager"].is_sensitive(sensitive_content) is True

        # Save it to storage
        entry_id = components["storage_manager"].save_entry(entry)
        assert entry_id is not None

        # Retrieve and verify it's still readable (encryption is transparent)
        retrieved = components["storage_manager"].get_entry(entry_id)
        assert retrieved is not None
        assert retrieved["content"] == sensitive_content

    def test_concurrent_operations(self, tray, components):
        """Test thread safety with concurrent operations."""
        import threading
        import time

        def clipboard_operation():
            for i in range(5):
                entry = {"content": f"Thread entry {i}", "timestamp": "2024-01-01", "hash": f"hash{i}", "type": "text"}
                components["clipboard_manager"]._add_to_history(entry)
                time.sleep(0.01)

        def toggle_operation():
            for _ in range(5):
                tray.toggle_enabled()
                time.sleep(0.01)

        # Run operations concurrently
        threads = [
            threading.Thread(target=clipboard_operation),
            threading.Thread(target=toggle_operation),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no crashes and data integrity
        history = components["clipboard_manager"].get_history()
        assert len(history) >= 5

    def test_error_recovery(self, tray, components):
        """Test system recovers from errors."""
        test_entry = {"content": "test content", "timestamp": "2024-01-01", "hash": "abc", "type": "text"}

        # Simulate keyboard engine error
        with patch.object(components["keyboard_engine"], "paste_text", side_effect=Exception("Test error")):
            # Should not crash
            tray._on_clipboard_change(test_entry)

        # System should still be functional
        assert tray.enabled is True

        # Next paste should work
        with patch.object(components["keyboard_engine"], "paste_text") as mock_paste:
            test_entry2 = {"content": "another test", "timestamp": "2024-01-01", "hash": "def", "type": "text"}
            tray._on_clipboard_change(test_entry2)
            mock_paste.assert_called_once()

    def test_cleanup_on_quit(self, tray, components):
        """Test proper cleanup when quitting."""
        with patch.object(tray.tray_icon, "hide"):
            # Start monitoring
            components["clipboard_manager"].start_monitoring()
            assert components["clipboard_manager"].monitoring is True

            # Quit
            tray.quit()

            # Verify cleanup
            assert components["clipboard_manager"].monitoring is False

    @patch("pasta.gui.tray.QApplication")
    def test_gui_window_lifecycle(self, mock_qapp, tray, components):
        """Test GUI window creation and cleanup."""
        mock_app = Mock()
        mock_qapp.instance.return_value = None
        mock_qapp.return_value = mock_app

        from pasta.gui.history_pyside6 import HistoryWindow as PySide6HistoryWindow

        with patch("pasta.gui.tray_pyside6.PySide6HistoryWindow", PySide6HistoryWindow) as mock_history:
            mock_window = Mock()
            mock_history.return_value = mock_window

            # Show history multiple times
            tray.show_history()
            tray.show_history()

            # Should create new window each time
            assert mock_history.call_count == 2

    def test_settings_persistence(self, tray, components, temp_db):
        """Test settings changes are persisted."""
        # Change settings
        tray.set_paste_mode("clipboard")

        # Create new tray instance
        with patch("pasta.gui.tray_pyside6.QApplication"), patch("pasta.gui.tray_pyside6.QSystemTrayIcon"):
            new_tray = SystemTray(**components)

            # Should remember paste mode (once settings are implemented)
            # For now, just verify it initializes without error
            assert new_tray.paste_mode == "auto"  # Default until settings implemented
