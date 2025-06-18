"""Additional tests for ClipboardManager to improve coverage."""

import threading
import time
from unittest.mock import Mock, patch

import pytest

from pasta.core.clipboard import ClipboardManager


class TestClipboardManagerCoverage:
    """Additional test cases for ClipboardManager coverage."""

    @pytest.fixture
    def manager(self):
        """Create a ClipboardManager instance for testing."""
        return ClipboardManager()

    def test_monitor_loop_error_handling(self, manager):
        """Test that _monitor_loop handles errors in _monitor_iteration."""
        # Make _monitor_iteration raise an exception
        with patch.object(manager, "_monitor_iteration", side_effect=Exception("Test error")):
            manager.monitoring = True

            # Start monitoring in a thread
            thread = threading.Thread(target=manager._monitor_loop)
            thread.start()

            # Let it run for a bit (should handle the exception)
            time.sleep(0.1)

            # Stop monitoring
            manager.monitoring = False
            thread.join(timeout=1)

            # Should complete without raising

    def test_monitor_iteration_callback_error(self, manager):
        """Test that callback errors don't stop monitoring."""
        # Add a callback that raises
        bad_callback = Mock(side_effect=Exception("Callback error"))
        manager.register_callback(bad_callback)

        with patch("pyperclip.paste", return_value="test content"):
            # Should not raise
            manager._monitor_iteration()

            # Callback should have been called despite raising
            bad_callback.assert_called_once()

    def test_monitor_iteration_pyperclip_error(self, manager):
        """Test that pyperclip errors are handled."""
        with patch("pyperclip.paste", side_effect=Exception("Clipboard error")):
            # Should not raise
            manager._monitor_iteration()

    def test_stop_monitoring_timeout(self, manager):
        """Test stop_monitoring with thread join timeout."""

        # Create a thread that won't stop quickly
        def slow_monitor():
            while manager.monitoring:
                time.sleep(0.1)

        manager.monitoring = True
        manager._monitor_thread = threading.Thread(target=slow_monitor)
        manager._monitor_thread.start()

        # Stop monitoring (will timeout on join)
        manager.stop_monitoring()

        # Should have stopped monitoring
        assert not manager.monitoring
