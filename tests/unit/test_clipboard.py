"""Tests for the ClipboardManager module."""

import hashlib
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager


class TestClipboardManager:
    """Test cases for ClipboardManager."""

    @pytest.fixture
    def manager(self):
        """Create a ClipboardManager instance for testing."""
        return ClipboardManager(history_size=10)

    def test_initialization(self, manager):
        """Test ClipboardManager initializes correctly."""
        assert manager.history == []
        assert manager.history_size == 10
        assert not manager.monitoring
        assert manager.callbacks == []
        assert manager._last_hash == ""

    def test_history_size_configuration(self):
        """Test history size can be configured."""
        manager = ClipboardManager(history_size=5)
        assert manager.history_size == 5

    def test_clipboard_monitoring_starts(self, manager):
        """Test that clipboard monitoring can be started."""
        with patch("threading.Thread") as mock_thread:
            manager.start_monitoring()
            assert manager.monitoring
            mock_thread.assert_called_once()
            # Verify thread is daemon
            call_kwargs = mock_thread.call_args.kwargs
            assert call_kwargs["daemon"] is True

    def test_clipboard_monitoring_doesnt_start_twice(self, manager):
        """Test that monitoring doesn't start if already running."""
        manager.monitoring = True
        with patch("threading.Thread") as mock_thread:
            manager.start_monitoring()
            mock_thread.assert_not_called()

    def test_stop_monitoring(self, manager):
        """Test that monitoring can be stopped."""
        manager.monitoring = True
        manager.stop_monitoring()
        assert not manager.monitoring

    @patch("pyperclip.paste")
    def test_clipboard_change_detection(self, mock_paste, manager):
        """Test that clipboard changes are detected."""
        # Set up clipboard content
        mock_paste.return_value = "test content"

        # Simulate monitoring loop iteration
        manager.monitoring = True
        manager._monitor_iteration()

        # Verify content was detected
        assert len(manager.history) == 1
        assert manager.history[0]["content"] == "test content"

    @patch("pyperclip.paste")
    def test_clipboard_empty_content_ignored(self, mock_paste, manager):
        """Test that empty clipboard content is ignored."""
        mock_paste.return_value = ""

        manager.monitoring = True
        manager._monitor_iteration()

        assert len(manager.history) == 0

    @patch("pyperclip.paste")
    def test_clipboard_whitespace_only_ignored(self, mock_paste, manager):
        """Test that whitespace-only content is ignored."""
        mock_paste.return_value = "   \n\t  "

        manager.monitoring = True
        manager._monitor_iteration()

        assert len(manager.history) == 0

    def test_content_type_detection_url(self, manager):
        """Test URL content type detection."""
        assert manager._detect_content_type("https://example.com") == "url"
        assert manager._detect_content_type("http://example.com") == "url"

    def test_content_type_detection_multiline(self, manager):
        """Test multiline content type detection."""
        assert manager._detect_content_type("line1\nline2") == "multiline"
        assert manager._detect_content_type("col1\tcol2") == "multiline"

    def test_content_type_detection_large_text(self, manager):
        """Test large text content type detection."""
        large_text = "x" * 501
        assert manager._detect_content_type(large_text) == "large_text"

    def test_content_type_detection_regular_text(self, manager):
        """Test regular text content type detection."""
        assert manager._detect_content_type("simple text") == "text"

    def test_history_deduplication(self, manager):
        """Test that duplicate entries are removed from history."""
        # Add an entry
        entry1 = {
            "content": "test",
            "timestamp": datetime.now(),
            "hash": hashlib.md5(b"test").hexdigest(),
            "type": "text",
        }
        manager._add_to_history(entry1)
        assert len(manager.history) == 1

        # Add duplicate (same hash)
        entry2 = {
            "content": "test",
            "timestamp": datetime.now(),
            "hash": hashlib.md5(b"test").hexdigest(),
            "type": "text",
        }
        manager._add_to_history(entry2)

        # Should still be only one entry
        assert len(manager.history) == 1

    def test_history_size_limit(self, manager):
        """Test that history respects size limit."""
        # Add more entries than history size
        for i in range(15):
            entry = {
                "content": f"content {i}",
                "timestamp": datetime.now(),
                "hash": hashlib.md5(f"content {i}".encode()).hexdigest(),
                "type": "text",
            }
            manager._add_to_history(entry)

        # History should be limited to 10
        assert len(manager.history) == 10
        # Most recent should be first
        assert manager.history[0]["content"] == "content 14"

    def test_callback_registration(self, manager):
        """Test callback registration."""
        callback = Mock()
        manager.register_callback(callback)
        assert callback in manager.callbacks

    @patch("pyperclip.paste")
    def test_callback_notification(self, mock_paste, manager):
        """Test that callbacks are notified on clipboard changes."""
        mock_paste.return_value = "new content"
        callback = Mock()
        manager.register_callback(callback)

        # Simulate monitoring
        manager.monitoring = True
        manager._monitor_iteration()

        # Callback should be called with the entry
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["content"] == "new content"

    @patch("pyperclip.paste")
    def test_multiple_callbacks(self, mock_paste, manager):
        """Test that multiple callbacks are all notified."""
        mock_paste.return_value = "test"
        callback1 = Mock()
        callback2 = Mock()
        manager.register_callback(callback1)
        manager.register_callback(callback2)

        manager.monitoring = True
        manager._monitor_iteration()

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_thread_safety_history_access(self, manager):
        """Test thread-safe access to history."""
        # This test verifies the manager has thread safety mechanisms
        # In the implementation, we'll need to add locks
        assert hasattr(manager, "_lock") or hasattr(manager, "_history_lock")

    @patch("pyperclip.paste")
    def test_error_handling_in_monitor_loop(self, mock_paste, manager):
        """Test that errors in monitoring don't crash the loop."""
        mock_paste.side_effect = Exception("Clipboard error")

        # Should not raise exception
        manager.monitoring = True
        manager._monitor_iteration()

        # History should remain empty due to error
        assert len(manager.history) == 0

    def test_get_history(self, manager):
        """Test getting history with optional limit."""
        # Add some entries
        for i in range(5):
            entry = {
                "content": f"content {i}",
                "timestamp": datetime.now(),
                "hash": hashlib.md5(f"content {i}".encode()).hexdigest(),
                "type": "text",
            }
            manager._add_to_history(entry)

        # Get all history
        assert len(manager.get_history()) == 5

        # Get limited history
        assert len(manager.get_history(limit=3)) == 3

        # Most recent should be first
        assert manager.get_history(limit=1)[0]["content"] == "content 4"

    def test_clear_history(self, manager):
        """Test clearing history."""
        # Add some entries
        for i in range(3):
            entry = {
                "content": f"content {i}",
                "timestamp": datetime.now(),
                "hash": f"hash{i}",
                "type": "text",
            }
            manager._add_to_history(entry)

        assert len(manager.history) == 3

        manager.clear_history()
        assert len(manager.history) == 0

    @patch("pyperclip.paste")
    def test_duplicate_content_not_added_consecutively(self, mock_paste, manager):
        """Test that same content isn't added twice in a row."""
        mock_paste.return_value = "same content"

        manager.monitoring = True

        # First iteration - should add
        manager._monitor_iteration()
        assert len(manager.history) == 1

        # Second iteration with same content - should not add
        manager._monitor_iteration()
        assert len(manager.history) == 1

    def test_entry_structure(self, manager):
        """Test that entries have the correct structure."""
        entry = {
            "content": "test",
            "timestamp": datetime.now(),
            "hash": "testhash",
            "type": "text",
        }
        manager._add_to_history(entry)

        stored_entry = manager.history[0]
        assert "content" in stored_entry
        assert "timestamp" in stored_entry
        assert "hash" in stored_entry
        assert "type" in stored_entry
        assert isinstance(stored_entry["timestamp"], datetime)
