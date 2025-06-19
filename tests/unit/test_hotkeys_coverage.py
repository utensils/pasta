"""Additional tests for HotkeyManager to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from pasta.core.hotkeys import HotkeyManager


class TestHotkeyManagerCoverage:
    """Additional test cases for HotkeyManager coverage."""

    @pytest.fixture
    def manager(self):
        """Create a HotkeyManager instance for testing."""
        return HotkeyManager()

    @patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", True)
    @patch("pasta.core.hotkeys.keyboard")
    def test_register_hotkeys_success(self, mock_keyboard, manager):
        """Test successful hotkey registration."""
        callback = Mock()
        manager.set_abort_callback(callback)

        # Register hotkeys
        manager.register_hotkeys()

        # Should call keyboard.add_hotkey with suppress=False
        mock_keyboard.add_hotkey.assert_called_once_with("esc", manager._check_double_esc, suppress=False)
        assert manager._registered is True

    @patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", True)
    @patch("pasta.core.hotkeys.keyboard")
    def test_register_hotkeys_exception(self, mock_keyboard, manager):
        """Test hotkey registration when keyboard.add_hotkey fails."""
        mock_keyboard.add_hotkey.side_effect = Exception("Failed")

        callback = Mock()
        manager.set_abort_callback(callback)

        # Should not raise
        manager.register_hotkeys()

        # Should not be registered
        assert manager._registered is False

    @patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", True)
    @patch("pasta.core.hotkeys.keyboard")
    def test_unregister_hotkeys_success(self, mock_keyboard, manager):
        """Test successful hotkey unregistration."""
        manager._registered = True

        # Unregister hotkeys
        manager.unregister_hotkeys()

        # Should call keyboard.remove_hotkey
        mock_keyboard.remove_hotkey.assert_called_once_with("esc+esc")
        assert manager._registered is False

    @patch("pasta.core.hotkeys.KEYBOARD_AVAILABLE", True)
    @patch("pasta.core.hotkeys.keyboard")
    def test_unregister_hotkeys_exception(self, mock_keyboard, manager):
        """Test hotkey unregistration when keyboard.remove_hotkey fails."""
        manager._registered = True
        mock_keyboard.remove_hotkey.side_effect = Exception("Failed")

        # Should not raise
        manager.unregister_hotkeys()

        # Should still mark as unregistered
        assert manager._registered is False

    def test_on_abort_hotkey_callback(self, manager):
        """Test abort hotkey triggers callback."""
        callback = Mock()
        manager.set_abort_callback(callback)

        # Trigger abort hotkey
        manager._on_abort_hotkey()

        # Callback should be called
        callback.assert_called_once()

    def test_on_abort_hotkey_callback_exception(self, manager):
        """Test abort hotkey when callback raises exception."""
        callback = Mock(side_effect=Exception("Callback error"))
        manager.set_abort_callback(callback)

        # Should not raise
        manager._on_abort_hotkey()

        # Callback should have been called
        callback.assert_called_once()

    def test_on_abort_hotkey_no_callback(self, manager):
        """Test abort hotkey when no callback is set."""
        # Should not raise
        manager._on_abort_hotkey()
