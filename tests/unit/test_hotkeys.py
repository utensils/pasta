"""Tests for the HotkeyManager module."""

from unittest.mock import Mock, patch

import pytest

from pasta.core.hotkeys import HotkeyManager


class TestHotkeyManager:
    """Test cases for HotkeyManager."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance for testing."""
        return HotkeyManager()

    def test_initialization(self, manager):
        """Test HotkeyManager initializes correctly."""
        assert manager.abort_callback is None
        assert manager.abort_hotkey == "esc+esc"
        assert not manager._registered
        assert hasattr(manager, "_lock")

    def test_set_abort_callback(self, manager):
        """Test setting abort callback."""
        callback = Mock()
        manager.set_abort_callback(callback)
        assert manager.abort_callback == callback

    @patch("pasta.core.hotkeys.keyboard.add_hotkey")
    def test_register_hotkeys(self, mock_add_hotkey, manager):
        """Test registering hotkeys."""
        manager.register_hotkeys()

        mock_add_hotkey.assert_called_once_with("esc+esc", manager._on_abort_hotkey, suppress=False)
        assert manager._registered

    @patch("pasta.core.hotkeys.keyboard.add_hotkey")
    def test_register_hotkeys_idempotent(self, mock_add_hotkey, manager):
        """Test that registering hotkeys is idempotent."""
        manager.register_hotkeys()
        manager.register_hotkeys()  # Second call

        # Should only be called once
        assert mock_add_hotkey.call_count == 1

    @patch("pasta.core.hotkeys.keyboard.add_hotkey", side_effect=Exception("Error"))
    def test_register_hotkeys_error_handling(self, mock_add_hotkey, manager):
        """Test error handling during hotkey registration."""
        # Should not raise exception
        manager.register_hotkeys()
        assert not manager._registered

    @patch("pasta.core.hotkeys.keyboard.remove_hotkey")
    def test_unregister_hotkeys(self, mock_remove_hotkey, manager):
        """Test unregistering hotkeys."""
        # First register
        manager._registered = True

        manager.unregister_hotkeys()

        mock_remove_hotkey.assert_called_once_with("esc+esc")
        assert not manager._registered

    @patch("pasta.core.hotkeys.keyboard.remove_hotkey")
    def test_unregister_hotkeys_not_registered(self, mock_remove_hotkey, manager):
        """Test unregistering when not registered."""
        manager.unregister_hotkeys()

        # Should not be called
        mock_remove_hotkey.assert_not_called()

    @patch("pasta.core.hotkeys.keyboard.remove_hotkey", side_effect=Exception("Error"))
    def test_unregister_hotkeys_error_handling(self, mock_remove_hotkey, manager):
        """Test error handling during hotkey unregistration."""
        manager._registered = True

        # Should not raise exception
        manager.unregister_hotkeys()
        # State should still be updated
        assert not manager._registered

    def test_on_abort_hotkey(self, manager):
        """Test abort hotkey handler."""
        callback = Mock()
        manager.set_abort_callback(callback)

        manager._on_abort_hotkey()

        callback.assert_called_once()

    def test_on_abort_hotkey_no_callback(self, manager):
        """Test abort hotkey handler with no callback."""
        # Should not raise exception
        manager._on_abort_hotkey()

    def test_on_abort_hotkey_callback_error(self, manager):
        """Test abort hotkey handler with callback error."""
        callback = Mock(side_effect=Exception("Callback error"))
        manager.set_abort_callback(callback)

        # Should not raise exception
        manager._on_abort_hotkey()
        callback.assert_called_once()

    def test_thread_safety(self, manager):
        """Test thread-safe operations."""
        import threading

        results = []

        def register_multiple():
            for _ in range(10):
                manager.register_hotkeys()
                results.append("registered")

        def unregister_multiple():
            for _ in range(10):
                manager.unregister_hotkeys()
                results.append("unregistered")

        threads = [
            threading.Thread(target=register_multiple),
            threading.Thread(target=unregister_multiple),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without deadlock
        assert len(results) == 20


class TestHotkeyManagerWithoutKeyboard:
    """Test cases for HotkeyManager when keyboard module is not available."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance for testing."""
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            return HotkeyManager()

    def test_register_hotkeys_without_keyboard(self, manager):
        """Test registering hotkeys when keyboard module is not available."""
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.register_hotkeys()

            # Should not be registered since keyboard is not available
            assert not manager._registered

    def test_unregister_hotkeys_without_keyboard(self, manager):
        """Test unregistering hotkeys when keyboard module is not available."""
        # Manually set registered state
        manager._registered = True

        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.unregister_hotkeys()

            # Should be unregistered
            assert not manager._registered

    @patch("pasta.core.hotkeys.keyboard.add_hotkey")
    def test_keyboard_not_called_when_unavailable(self, mock_add_hotkey, manager):
        """Test that keyboard methods are not called when module is unavailable."""
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.register_hotkeys()

            # Keyboard methods should not be called
            mock_add_hotkey.assert_not_called()

    @patch("pasta.core.hotkeys.keyboard.remove_hotkey")
    def test_keyboard_remove_not_called_when_unavailable(self, mock_remove_hotkey, manager):
        """Test that keyboard remove is not called when module is unavailable."""
        manager._registered = True

        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.unregister_hotkeys()

            # Keyboard methods should not be called
            mock_remove_hotkey.assert_not_called()
