"""End-to-end integration tests for clipboard monitoring flow."""

import contextlib
import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray


class TestClipboardMonitoringE2E:
    """End-to-end tests for clipboard monitoring functionality."""

    @pytest.fixture(autouse=True)
    def isolate_tests(self):
        """Ensure test isolation by clearing any global state."""
        # Clear clipboard before test
        with contextlib.suppress(Exception):
            import pyperclip

            pyperclip.copy("")
        yield
        # Clear clipboard after test
        with contextlib.suppress(Exception):
            pyperclip.copy("")

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test_e2e.db")

    @pytest.fixture
    def storage_manager(self, temp_db):
        """Create real storage manager."""
        return StorageManager(temp_db)

    @pytest.fixture
    def clipboard_manager(self):
        """Create real clipboard manager."""
        manager = ClipboardManager()
        # Ensure clean state
        manager.clear_history()
        manager._last_hash = ""
        yield manager
        # Ensure cleanup
        if manager.monitoring:
            manager.stop_monitoring()

    @pytest.fixture
    def mock_system_components(self):
        """Mock system components to prevent GUI creation."""
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
            yield

    def test_full_clipboard_to_storage_flow(self, clipboard_manager, storage_manager):
        """Test complete flow from clipboard change to database storage."""
        # Track callback invocations
        callback_called = threading.Event()
        saved_entries = []

        def on_clipboard_change(entry):
            """Callback to save clipboard entry."""
            saved_id = storage_manager.save_entry(entry)
            saved_entries.append((saved_id, entry))
            callback_called.set()

        # Register callback
        clipboard_manager.register_callback(on_clipboard_change)

        # Start monitoring
        clipboard_manager.start_monitoring()
        assert clipboard_manager.monitoring is True

        try:
            # Simulate clipboard content
            test_content = "Test clipboard content for E2E"
            with patch("pyperclip.paste", return_value=test_content):
                # Trigger clipboard check manually
                clipboard_manager._monitor_iteration()

            # Wait for callback
            assert callback_called.wait(timeout=2), "Callback was not called within timeout"

            # Verify entry was saved
            assert len(saved_entries) == 1
            entry_id, entry = saved_entries[0]
            assert entry_id is not None
            assert entry["content"] == test_content
            assert entry["content_type"] == "text"

            # Verify entry is in storage
            stored_entry = storage_manager.get_entry(entry_id)
            assert stored_entry is not None
            assert stored_entry["content"] == test_content

            # Verify entry is in history
            history = clipboard_manager.get_history()
            assert len(history) >= 1
            assert history[0]["content"] == test_content

        finally:
            clipboard_manager.stop_monitoring()
            assert clipboard_manager.monitoring is False

    def test_concurrent_clipboard_operations(self, clipboard_manager, storage_manager):
        """Test thread safety with concurrent clipboard operations."""
        # Track all saved entries
        saved_entries = []
        lock = threading.Lock()

        def on_clipboard_change(entry):
            """Thread-safe callback."""
            entry_id = storage_manager.save_entry(entry)
            with lock:
                saved_entries.append(entry_id)

        clipboard_manager.register_callback(on_clipboard_change)
        # Don't start background monitoring to avoid interference
        # clipboard_manager.start_monitoring()

        try:
            # Simulate multiple concurrent clipboard changes
            def simulate_clipboard_change(content):
                with patch("pyperclip.paste", return_value=content):
                    clipboard_manager._monitor_iteration()
                time.sleep(0.01)  # Small delay to allow processing

            threads = []
            for i in range(10):
                t = threading.Thread(target=simulate_clipboard_change, args=(f"Concurrent content {i}",))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # Give a moment for all callbacks to complete
            time.sleep(0.5)

            # Verify all entries were saved
            assert len(saved_entries) == 10
            assert all(entry_id is not None for entry_id in saved_entries)

            # Verify database integrity
            all_entries = storage_manager.get_entries(limit=20)
            assert len(all_entries) >= 10

        finally:
            # clipboard_manager.stop_monitoring()
            pass

    def test_clipboard_monitoring_with_errors(self, clipboard_manager, storage_manager):
        """Test error handling in clipboard monitoring flow."""
        error_count = 0
        success_count = 0

        def on_clipboard_change(entry):
            """Callback that sometimes fails."""
            nonlocal error_count, success_count
            if entry["content"].startswith("Error"):
                error_count += 1
                raise Exception("Simulated error")
            else:
                storage_manager.save_entry(entry)
                success_count += 1

        clipboard_manager.register_callback(on_clipboard_change)
        # Don't start background monitoring to avoid interference
        # clipboard_manager.start_monitoring()

        try:
            # Test with error-inducing content
            with patch("pyperclip.paste", return_value="Error: This will fail"):
                clipboard_manager._monitor_iteration()

            time.sleep(0.1)  # Small delay between changes

            # Test with normal content
            with patch("pyperclip.paste", return_value="This will succeed"):
                clipboard_manager._monitor_iteration()

            # Give time for processing
            time.sleep(0.2)

            # Verify error was handled gracefully
            assert error_count == 1
            assert success_count == 1
            # clipboard_manager.monitoring is False since we didn't start it

        finally:
            # clipboard_manager.stop_monitoring()
            pass

    def test_clipboard_history_limits(self, clipboard_manager):
        """Test clipboard history size limits."""
        # Start monitoring
        clipboard_manager.start_monitoring()

        try:
            # Add many entries
            for i in range(150):  # More than default limit
                with patch("pyperclip.paste", return_value=f"Entry {i}"):
                    clipboard_manager._monitor_iteration()
                time.sleep(0.001)  # Small delay to ensure different timestamps

            # Check history is limited
            history = clipboard_manager.get_history()
            assert len(history) <= 100  # Default max history size

            # Verify newest entries are kept
            assert any("Entry 149" in h["content"] for h in history)
            assert not any("Entry 0" in h["content"] for h in history)

        finally:
            # clipboard_manager.stop_monitoring()
            pass

    def test_clipboard_duplicate_detection(self, clipboard_manager, storage_manager):
        """Test that duplicate clipboard content is handled correctly."""
        saved_entries = []

        def on_clipboard_change(entry):
            saved_entries.append(entry)
            storage_manager.save_entry(entry)

        clipboard_manager.register_callback(on_clipboard_change)
        # Don't start background monitoring to avoid interference
        # clipboard_manager.start_monitoring()

        try:
            # Set same content multiple times
            test_content = "Duplicate content test"
            for _ in range(5):
                with patch("pyperclip.paste", return_value=test_content):
                    clipboard_manager._monitor_iteration()
                time.sleep(0.1)

            # Should only save once (duplicate detection)
            assert len(saved_entries) == 1
            assert saved_entries[0]["content"] == test_content

        finally:
            # clipboard_manager.stop_monitoring()
            pass

    def test_clipboard_content_types(self, clipboard_manager, storage_manager):
        """Test handling of different content types."""
        saved_entries = []

        def on_clipboard_change(entry):
            saved_entries.append(entry)
            storage_manager.save_entry(entry)

        clipboard_manager.register_callback(on_clipboard_change)
        # Don't start background monitoring to avoid interference
        # clipboard_manager.start_monitoring()

        try:
            # Test different content types
            test_cases = [
                ("Plain text content", "text"),
                ("https://example.com/page", "url"),  # URLs are detected as url type
                ("Multi\nline\ntext", "multiline"),  # Multiline text has its own type
                ("😀 Unicode emoji content 🎉", "text"),
                ("    Leading whitespace", "text"),
            ]

            for content, expected_type in test_cases:
                saved_entries.clear()
                with patch("pyperclip.paste", return_value=content):
                    clipboard_manager._monitor_iteration()
                time.sleep(0.1)

                assert len(saved_entries) == 1
                assert saved_entries[0]["content"] == content
                assert saved_entries[0]["content_type"] == expected_type

        finally:
            # clipboard_manager.stop_monitoring()
            pass

    @patch("pasta.gui.tray_pyside6.ClipboardWorker")
    def test_system_tray_clipboard_integration(self, mock_worker_class, clipboard_manager, storage_manager, mock_system_components):
        """Test clipboard monitoring through SystemTray integration."""
        # Create worker that will call clipboard callbacks
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        # Track worker initialization
        def worker_init_side_effect(clipboard_manager):
            # Register the worker's callback
            clipboard_manager.register_callback(mock_worker._on_clipboard_change)
            return mock_worker

        mock_worker_class.side_effect = worker_init_side_effect

        # Create SystemTray
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.utils.permissions import PermissionChecker

        tray = SystemTray(
            clipboard_manager=clipboard_manager,
            keyboard_engine=PastaKeyboardEngine(),
            storage_manager=storage_manager,
            permission_checker=PermissionChecker(),
        )

        # Simulate clipboard change through worker
        test_entry = {
            "content": "SystemTray integration test",
            "timestamp": datetime.now().isoformat(),
            "hash": "test123",
            "content_type": "text",
        }

        # The worker would normally emit this to the tray
        tray._on_clipboard_change(test_entry)

        # Verify it was saved
        entries = storage_manager.get_entries()
        assert any(e["content"] == "SystemTray integration test" for e in entries)

    def test_clipboard_monitoring_performance(self, clipboard_manager):
        """Test clipboard monitoring performance with rapid changes."""
        clipboard_manager.start_monitoring()
        change_times = []

        try:
            # Simulate rapid clipboard changes
            start_time = time.time()
            for i in range(50):
                with patch("pyperclip.paste", return_value=f"Rapid change {i}"):
                    before = time.time()
                    clipboard_manager._monitor_iteration()
                    after = time.time()
                    change_times.append(after - before)

            total_time = time.time() - start_time

            # Performance assertions
            assert total_time < 5.0  # Should handle 50 changes in under 5 seconds
            assert max(change_times) < 0.5  # No single change should take > 500ms
            avg_time = sum(change_times) / len(change_times)
            assert avg_time < 0.1  # Average should be under 100ms

        finally:
            # clipboard_manager.stop_monitoring()
            pass
