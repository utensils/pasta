"""Tests for the PySide6 Settings window module."""

from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox

from pasta.core.settings import Settings, SettingsManager
from pasta.gui.settings_pyside6 import SettingsWindow


class TestSettingsWindow:
    """Test cases for PySide6 SettingsWindow."""

    @pytest.fixture
    def settings_manager(self):
        """Create a real SettingsManager with test settings."""
        manager = SettingsManager()
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
        assert window.width() == 600
        assert window.height() == 500

    def test_tabs_created(self, window):
        """Test all tabs are created."""
        tab_titles = []
        for i in range(window.tabs.count()):
            tab_titles.append(window.tabs.tabText(i))

        expected_tabs = ["General", "Performance", "History", "Privacy", "Hotkeys"]
        assert tab_titles == expected_tabs

    def test_general_tab_widgets(self, window):
        """Test General tab widgets are initialized correctly."""
        assert window.start_on_login.isChecked() is False
        assert window.monitoring_enabled.isChecked() is True
        assert window.paste_mode.currentText() == "auto"

    def test_performance_tab_widgets(self, window):
        """Test Performance tab widgets are initialized correctly."""
        assert window.typing_speed.value() == 100
        assert window.speed_label.text() == "100 chars/sec"
        assert window.chunk_size.value() == 200
        assert window.adaptive_delay.isChecked() is True

    def test_history_tab_widgets(self, window):
        """Test History tab widgets are initialized correctly."""
        assert window.history_size.value() == 100
        assert window.history_retention.value() == 7
        assert window.encrypt_sensitive.isChecked() is True

    def test_privacy_tab_widgets(self, window):
        """Test Privacy tab widgets are initialized correctly."""
        assert window.privacy_mode.isChecked() is False
        assert window.excluded_apps_list.count() == 2
        assert window.excluded_apps_list.item(0).text() == "password_manager"
        assert window.excluded_apps_list.item(1).text() == "keychain"
        assert window.excluded_patterns.toPlainText() == "api_key\npassword"

    def test_hotkeys_tab_widgets(self, window):
        """Test Hotkeys tab widgets are initialized correctly."""
        assert window.emergency_stop_hotkey.text() == "esc+esc"
        assert window.quick_paste_hotkey.text() == "ctrl+shift+v"
        assert window.toggle_monitoring_hotkey.text() == "ctrl+shift+m"

    def test_typing_speed_slider_updates_label(self, window):
        """Test typing speed slider updates the label."""
        window.typing_speed.setValue(250)
        assert window.speed_label.text() == "250 chars/sec"

    def test_paste_mode_selection(self, window):
        """Test paste mode combo box."""
        # Test all options
        window.paste_mode.setCurrentIndex(1)
        assert window.paste_mode.currentText() == "clipboard"

        window.paste_mode.setCurrentIndex(2)
        assert window.paste_mode.currentText() == "typing"

    def test_add_excluded_app(self, window, qtbot):
        """Test adding an excluded app."""
        initial_count = window.excluded_apps_list.count()

        # Mock input dialog
        with patch.object(QInputDialog, "getText") as mock_dialog:
            mock_dialog.return_value = ("new_app", True)

            # Click add button
            qtbot.mouseClick(window.add_app_button, Qt.MouseButton.LeftButton)

            # Should add the app
            assert window.excluded_apps_list.count() == initial_count + 1
            assert window.excluded_apps_list.item(initial_count).text() == "new_app"

    def test_add_excluded_app_cancelled(self, window, qtbot):
        """Test cancelling add excluded app dialog."""
        initial_count = window.excluded_apps_list.count()

        # Mock input dialog - cancelled
        with patch.object(QInputDialog, "getText") as mock_dialog:
            mock_dialog.return_value = ("", False)

            # Click add button
            qtbot.mouseClick(window.add_app_button, Qt.MouseButton.LeftButton)

            # Should not add anything
            assert window.excluded_apps_list.count() == initial_count

    def test_remove_excluded_app(self, window, qtbot):
        """Test removing an excluded app."""
        initial_count = window.excluded_apps_list.count()

        # Select first item
        window.excluded_apps_list.setCurrentRow(0)

        # Click remove button
        qtbot.mouseClick(window.remove_app_button, Qt.MouseButton.LeftButton)

        # Should remove the app
        assert window.excluded_apps_list.count() == initial_count - 1

    def test_remove_excluded_app_no_selection(self, window, qtbot):
        """Test removing when no app is selected."""
        initial_count = window.excluded_apps_list.count()

        # Clear selection
        window.excluded_apps_list.clearSelection()

        # Click remove button
        qtbot.mouseClick(window.remove_app_button, Qt.MouseButton.LeftButton)

        # Should not remove anything
        assert window.excluded_apps_list.count() == initial_count

    def test_save_settings(self, window, settings_manager, qtbot):
        """Test saving settings."""
        # Change some values
        window.typing_speed.setValue(150)
        window.adaptive_delay.setChecked(False)
        window.privacy_mode.setChecked(True)

        # Mock accept method and QMessageBox
        with patch.object(window, "accept") as mock_accept, patch.object(QMessageBox, "information"):
            # Click save button
            qtbot.mouseClick(window.ok_button, Qt.MouseButton.LeftButton)

            # Should call accept
            mock_accept.assert_called_once()

        # Check settings were updated
        assert settings_manager.settings.typing_speed == 150
        assert settings_manager.settings.adaptive_delay is False
        assert settings_manager.settings.privacy_mode is True

    def test_cancel_button(self, window, qtbot):
        """Test cancel button closes without saving."""
        # Change a value
        window.typing_speed.setValue(150)

        # Mock reject method
        with patch.object(window, "reject") as mock_reject:
            # Click cancel button
            qtbot.mouseClick(window.cancel_button, Qt.MouseButton.LeftButton)

            # Should call reject
            mock_reject.assert_called_once()

    def test_excluded_patterns_text_edit(self, window, settings_manager):
        """Test excluded patterns text edit."""
        # Change patterns
        new_patterns = "secret\ntoken\ncredential"
        window.excluded_patterns.setPlainText(new_patterns)

        # Apply settings
        with patch.object(QMessageBox, "information"):
            window.apply_settings()

        # Check settings were updated
        assert settings_manager.settings.excluded_patterns == ["secret", "token", "credential"]

    def test_empty_excluded_patterns(self, window, settings_manager):
        """Test empty excluded patterns."""
        # Clear patterns
        window.excluded_patterns.clear()

        # Apply settings
        with patch.object(QMessageBox, "information"):
            window.apply_settings()

        # Check settings were updated
        assert settings_manager.settings.excluded_patterns == []

    def test_hotkey_validation(self, window):
        """Test hotkey field validation."""
        # Valid hotkey
        window.emergency_stop_hotkey.setText("ctrl+alt+x")
        assert window.emergency_stop_hotkey.text() == "ctrl+alt+x"

        # Empty hotkey is allowed (disables the hotkey)
        window.emergency_stop_hotkey.clear()
        assert window.emergency_stop_hotkey.text() == ""

    def test_privacy_mode_interaction(self, window, settings_manager):
        """Test privacy mode checkbox interaction."""
        # Initially privacy mode is off
        assert window.privacy_mode.isChecked() is False

        # Toggle on
        window.privacy_mode.setChecked(True)

        # Apply settings
        with patch.object(QMessageBox, "information"):
            window.apply_settings()

        # Check settings were updated
        assert settings_manager.settings.privacy_mode is True

    def test_monitoring_enabled_toggle(self, window, settings_manager):
        """Test monitoring enabled checkbox."""
        # Initially monitoring is enabled
        assert window.monitoring_enabled.isChecked() is True

        # Toggle off
        window.monitoring_enabled.setChecked(False)

        # Apply settings
        with patch.object(QMessageBox, "information"):
            window.apply_settings()

        # Check settings were updated
        assert settings_manager.settings.monitoring_enabled is False

    def test_start_on_login_toggle(self, window, settings_manager):
        """Test start on login checkbox."""
        # Initially start on login is off
        assert window.start_on_login.isChecked() is False

        # Toggle on
        window.start_on_login.setChecked(True)

        # Apply settings
        with patch.object(QMessageBox, "information"):
            window.apply_settings()

        # Check settings were updated
        assert settings_manager.settings.start_on_login is True

    def test_history_retention_value(self, window, settings_manager):
        """Test history retention spin box."""
        # Check default value
        assert window.history_retention.value() == 30  # Default from settings

        # Test range
        assert window.history_retention.minimum() == 1
        assert window.history_retention.maximum() == 365

        # Set a new value
        window.history_retention.setValue(90)
        assert window.history_retention.value() == 90
