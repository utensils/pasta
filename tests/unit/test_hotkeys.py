"""Tests for the HotkeyManager module."""

import sys
import threading
from unittest.mock import Mock, patch

import pytest

from pasta.core.hotkeys import KEYBOARD_AVAILABLE, HotkeyManager


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

    def test_keyboard_module_disabled_on_macos(self):
        """Test that keyboard module is disabled on macOS to prevent crashes."""
        if sys.platform == "darwin":
            assert not KEYBOARD_AVAILABLE
        # On other platforms, it depends on whether keyboard is installed

    def test_set_abort_callback(self, manager):
        """Test setting abort callback."""
        callback = Mock()
        manager.set_abort_callback(callback)
        assert manager.abort_callback == callback

    @pytest.mark.skipif(sys.platform == "darwin", reason="Keyboard module disabled on macOS")
    def test_register_hotkeys(self, manager):
        """Test registering hotkeys."""
        if not KEYBOARD_AVAILABLE:
            pytest.skip("Keyboard module not available")

        with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
            manager.register_hotkeys()
            mock_keyboard.add_hotkey.assert_called_once_with("esc", manager._check_double_esc, suppress=False)
            assert manager._registered

    def test_register_hotkeys_idempotent(self, manager):
        """Test that registering hotkeys is idempotent."""
        manager._registered = True

        if sys.platform != "darwin" and KEYBOARD_AVAILABLE:
            with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
                manager.register_hotkeys()
                # Should not call add_hotkey if already registered
                mock_keyboard.add_hotkey.assert_not_called()
        else:
            # Should not raise exception
            manager.register_hotkeys()

    @pytest.mark.skipif(sys.platform == "darwin", reason="Keyboard module disabled on macOS")
    def test_register_hotkeys_error_handling(self, manager):
        """Test error handling during hotkey registration."""
        if not KEYBOARD_AVAILABLE:
            pytest.skip("Keyboard module not available")

        with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
            mock_keyboard.add_hotkey.side_effect = Exception("Test error")
            # Should not raise exception
            manager.register_hotkeys()
            assert not manager._registered

    @pytest.mark.skipif(sys.platform == "darwin", reason="Keyboard module disabled on macOS")
    def test_unregister_hotkeys(self, manager):
        """Test unregistering hotkeys."""
        if not KEYBOARD_AVAILABLE:
            pytest.skip("Keyboard module not available")

        manager._registered = True
        with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
            manager.unregister_hotkeys()
            mock_keyboard.remove_hotkey.assert_called_once_with("esc+esc")
            assert not manager._registered

    def test_unregister_hotkeys_not_registered(self, manager):
        """Test unregistering when not registered."""
        manager._registered = False

        if sys.platform != "darwin" and KEYBOARD_AVAILABLE:
            with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
                manager.unregister_hotkeys()
                mock_keyboard.remove_hotkey.assert_not_called()
        else:
            # Should not raise exception
            manager.unregister_hotkeys()

    @pytest.mark.skipif(sys.platform == "darwin", reason="Keyboard module disabled on macOS")
    def test_unregister_hotkeys_error_handling(self, manager):
        """Test error handling during hotkey unregistration."""
        if not KEYBOARD_AVAILABLE:
            pytest.skip("Keyboard module not available")

        manager._registered = True
        with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
            mock_keyboard.remove_hotkey.side_effect = Exception("Test error")
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

    def test_macos_regression_no_crash(self):
        """Regression test: Ensure no CoreFoundation crash on macOS."""
        if sys.platform != "darwin":
            pytest.skip("macOS-specific test")

        # This should not crash
        manager = HotkeyManager()
        manager.register_hotkeys()
        manager.unregister_hotkeys()

        # Verify keyboard module is not imported on macOS
        assert not KEYBOARD_AVAILABLE


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

    def test_keyboard_not_called_when_unavailable(self, manager):
        """Test that keyboard methods are not called when module is unavailable."""
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            # Should not raise exception
            manager.register_hotkeys()
            assert not manager._registered

    def test_keyboard_remove_not_called_when_unavailable(self, manager):
        """Test that keyboard remove is not called when module is unavailable."""
        manager._registered = True

        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            # Should handle gracefully
            manager.unregister_hotkeys()
            assert not manager._registered
