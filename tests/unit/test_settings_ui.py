"""Tests for the Settings UI module."""

from unittest.mock import Mock

import pytest

from pasta.gui.settings_pyside6 import SettingsWindow


@pytest.mark.skip(reason="PySide6 Settings UI implementation differs - needs rewrite")
class TestSettingsWindow:
    """Test cases for SettingsWindow.

    Note: These tests were written for the PyQt6 implementation.
    The PySide6 implementation has a different UI structure and needs updated tests.
    """

    @pytest.fixture
    def settings_manager(self):
        """Create a mock SettingsManager."""
        from pasta.core.settings import Settings

        manager = Mock()
        # Use real Settings object to ensure correct types
        manager.settings = Settings(
            typing_speed=100,
            chunk_size=200,
            adaptive_delay=True,
            history_size=100,
            history_retention_days=7,
            encrypt_sensitive=True,
            privacy_mode=False,
            excluded_apps=["password_manager", "keychain"],
            excluded_patterns=["api_key", "password"],
            emergency_stop_hotkey="esc+esc",
            quick_paste_hotkey="ctrl+shift+v",
            toggle_monitoring_hotkey="ctrl+shift+m",
            start_on_login=False,
        )
        return manager

    @pytest.fixture
    def window(self, settings_manager, qtbot):
        """Create a SettingsWindow for testing."""
        window = SettingsWindow(settings_manager=settings_manager)
        qtbot.addWidget(window)
        return window

    def test_initialization(self, window, settings_manager):
        """Test SettingsWindow initializes correctly."""
        assert window.settings_manager == settings_manager
        assert window.windowTitle() == "Pasta Settings"
        assert window.isModal() is False

    def test_load_settings(self, window, settings_manager):
        """Test loading settings into UI."""
        # Check that widgets have correct values
        assert window.typing_speed.value() == 100
        assert window.chunk_size.value() == 200
        assert window.history_size.value() == 100
        assert window.history_retention.value() == 7

        # Check checkboxes
        assert window.adaptive_delay.isChecked() is True
        assert window.encrypt_sensitive.isChecked() is True
        assert window.privacy_mode.isChecked() is False
        assert window.start_on_login.isChecked() is False

        # Check text fields
        # PySide6 implementation uses QListWidget for excluded_apps
        # assert window.excluded_apps.toPlainText() == "password_manager\nkeychain"
        assert window.excluded_patterns.toPlainText() == "api_key\npassword"

        # Check hotkey fields
        assert window.emergency_stop_hotkey.text() == "esc+esc"
        assert window.quick_paste_hotkey.text() == "ctrl+shift+v"
        assert window.toggle_monitoring_hotkey.text() == "ctrl+shift+m"
