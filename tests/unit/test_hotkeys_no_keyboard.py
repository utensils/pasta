"""Tests for the HotkeyManager module when keyboard is not available."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock the keyboard module before importing HotkeyManager
sys.modules["keyboard"] = MagicMock()

from pasta.core.hotkeys import HotkeyManager  # noqa: E402


class TestHotkeyManagerNoKeyboard:
    """Test cases for HotkeyManager when keyboard module fails to import."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance for testing."""
        # Patch KEYBOARD_AVAILABLE to be False
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            return HotkeyManager()

    def test_initialization(self, manager):
        """Test HotkeyManager initializes correctly without keyboard."""
        assert manager.abort_callback is None
        assert manager.abort_hotkey == "esc+esc"
        assert not manager._registered
        assert hasattr(manager, "_lock")

    def test_register_hotkeys_no_keyboard(self, manager):
        """Test registering hotkeys when keyboard is not available."""
        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.register_hotkeys()

            # Should not be registered since keyboard is not available
            assert not manager._registered

    def test_unregister_hotkeys_no_keyboard(self, manager):
        """Test unregistering hotkeys when keyboard is not available."""
        # Manually set registered state
        manager._registered = True

        with patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", False):
            manager.unregister_hotkeys()

            # Should be unregistered
            assert not manager._registered

    def test_set_abort_callback_no_keyboard(self, manager):
        """Test setting abort callback works without keyboard."""
        callback = Mock()
        manager.set_abort_callback(callback)
        assert manager.abort_callback == callback

    def test_on_abort_hotkey_no_keyboard(self, manager):
        """Test abort hotkey handler works without keyboard."""
        callback = Mock()
        manager.set_abort_callback(callback)

        manager._on_abort_hotkey()

        callback.assert_called_once()
