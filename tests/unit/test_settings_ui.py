"""Tests for the Settings UI module."""

from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt

from pasta.gui.settings import SettingsWindow


class TestSettingsWindow:
    """Test cases for SettingsWindow."""

    @pytest.fixture
    def settings_manager(self):
        """Create a mock SettingsManager."""
        manager = Mock()
        manager.settings = Mock(
            typing_speed=100,
            chunk_size=200,
            history_size=100,
            history_retention_days=7,
            paste_mode="auto",
            monitoring_enabled=True,
            start_on_login=False,
            privacy_mode=False,
            encrypt_sensitive=True,
            adaptive_delay=True,
            excluded_apps=[],
            emergency_stop_hotkey="esc+esc",
            quick_paste_hotkey="",
            toggle_monitoring_hotkey="",
        )
        return manager

    @pytest.fixture
    def window(self, qtbot, settings_manager):
        """Create a SettingsWindow for testing."""
        window = SettingsWindow(settings_manager=settings_manager)
        qtbot.addWidget(window)
        return window

    def test_initialization(self, window, settings_manager):
        """Test SettingsWindow initializes correctly."""
        assert window.settings_manager == settings_manager
        assert window.windowTitle() == "Pasta - Settings"
        assert window.isVisible() is False

    def test_ui_elements_created(self, window):
        """Test all UI elements are created."""
        # Performance settings
        assert hasattr(window, "typing_speed_spin")
        assert hasattr(window, "chunk_size_spin")
        assert hasattr(window, "adaptive_delay_checkbox")

        # History settings
        assert hasattr(window, "history_size_spin")
        assert hasattr(window, "retention_days_spin")
        assert hasattr(window, "encrypt_sensitive_checkbox")

        # General settings
        assert hasattr(window, "paste_mode_combo")
        assert hasattr(window, "monitoring_enabled_checkbox")
        assert hasattr(window, "start_on_login_checkbox")
        assert hasattr(window, "privacy_mode_checkbox")

        # Buttons
        assert hasattr(window, "save_button")
        assert hasattr(window, "cancel_button")
        assert hasattr(window, "apply_button")
        assert hasattr(window, "reset_button")

    def test_load_settings(self, window, settings_manager):
        """Test loading settings into UI."""
        window.load_settings()

        # Check values are loaded
        assert window.typing_speed_spin.value() == 100
        assert window.chunk_size_spin.value() == 200
        assert window.history_size_spin.value() == 100
        assert window.retention_days_spin.value() == 7
        assert window.paste_mode_combo.currentText() == "Auto"
        assert window.monitoring_enabled_checkbox.isChecked() is True
        assert window.start_on_login_checkbox.isChecked() is False
        assert window.privacy_mode_checkbox.isChecked() is False
        assert window.encrypt_sensitive_checkbox.isChecked() is True
        assert window.adaptive_delay_checkbox.isChecked() is True

    def test_save_settings(self, window, settings_manager, qtbot):
        """Test saving settings from UI."""
        # Change some values
        window.typing_speed_spin.setValue(200)
        window.privacy_mode_checkbox.setChecked(True)
        window.paste_mode_combo.setCurrentIndex(1)  # Clipboard

        # Click save
        qtbot.mouseClick(window.save_button, Qt.MouseButton.LeftButton)

        # Check update was called with correct values
        settings_manager.update.assert_called_once()
        call_args = settings_manager.update.call_args[1]
        assert call_args["typing_speed"] == 200
        assert call_args["privacy_mode"] is True
        assert call_args["paste_mode"] == "clipboard"

        # Window should close
        assert window.isVisible() is False

    def test_cancel_settings(self, window, settings_manager, qtbot):
        """Test canceling changes."""
        # Change some values
        window.typing_speed_spin.setValue(200)

        # Click cancel
        qtbot.mouseClick(window.cancel_button, Qt.MouseButton.LeftButton)

        # Settings should not be updated
        settings_manager.update.assert_not_called()

        # Window should close
        assert window.isVisible() is False

    def test_apply_settings(self, window, settings_manager, qtbot):
        """Test applying settings without closing."""
        # Change value
        window.typing_speed_spin.setValue(150)

        # Click apply
        qtbot.mouseClick(window.apply_button, Qt.MouseButton.LeftButton)

        # Settings should be updated
        settings_manager.update.assert_called_once()
        call_args = settings_manager.update.call_args[1]
        assert call_args["typing_speed"] == 150

        # Window should remain open
        assert window.isVisible() is True

    def test_reset_defaults(self, window, settings_manager, qtbot):
        """Test resetting to defaults."""
        # Change some values
        window.typing_speed_spin.setValue(200)
        window.privacy_mode_checkbox.setChecked(True)

        # Click reset
        qtbot.mouseClick(window.reset_button, Qt.MouseButton.LeftButton)

        # Should reset settings manager
        settings_manager.reset_to_defaults.assert_called_once()

        # Should reload UI
        window.load_settings()
        assert window.typing_speed_spin.value() == 100  # Default

    def test_validation_typing_speed(self, window, qtbot):
        """Test typing speed validation."""
        # Valid range is 1-1000
        window.typing_speed_spin.setValue(0)
        assert window.typing_speed_spin.value() == 1  # Should clamp to min

        window.typing_speed_spin.setValue(2000)
        assert window.typing_speed_spin.value() == 1000  # Should clamp to max

    def test_validation_history_size(self, window, qtbot):
        """Test history size validation."""
        # Valid range is 1-10000
        window.history_size_spin.setValue(0)
        assert window.history_size_spin.value() == 1

        window.history_size_spin.setValue(20000)
        assert window.history_size_spin.value() == 10000

    def test_paste_mode_options(self, window):
        """Test paste mode combo box options."""
        combo = window.paste_mode_combo
        assert combo.count() == 3
        assert combo.itemText(0) == "Auto"
        assert combo.itemText(1) == "Clipboard"
        assert combo.itemText(2) == "Typing"

    def test_excluded_apps_list(self, window, qtbot):
        """Test excluded apps list management."""
        # Add app
        window.excluded_app_input.setText("notepad.exe")
        qtbot.mouseClick(window.add_excluded_app_button, Qt.MouseButton.LeftButton)

        assert window.excluded_apps_list.count() == 1
        assert window.excluded_apps_list.item(0).text() == "notepad.exe"

        # Remove app
        window.excluded_apps_list.setCurrentRow(0)
        qtbot.mouseClick(window.remove_excluded_app_button, Qt.MouseButton.LeftButton)

        assert window.excluded_apps_list.count() == 0

    def test_hotkey_configuration(self, window, settings_manager):
        """Test hotkey configuration fields."""
        # Check initial values
        assert window.emergency_stop_hotkey_input.text() == "esc+esc"
        assert window.quick_paste_hotkey_input.text() == ""
        assert window.toggle_monitoring_hotkey_input.text() == ""

        # Change hotkey
        window.emergency_stop_hotkey_input.setText("ctrl+shift+x")
        window.save_settings()

        # Check it was saved
        call_args = settings_manager.update.call_args[1]
        assert call_args["emergency_stop_hotkey"] == "ctrl+shift+x"

    def test_settings_changed_indicator(self, window, qtbot):
        """Test indicator shows when settings are changed."""
        # Initially not changed
        assert not window.has_unsaved_changes()

        # Change a value
        window.typing_speed_spin.setValue(200)
        assert window.has_unsaved_changes()

        # Apply changes
        qtbot.mouseClick(window.apply_button, Qt.MouseButton.LeftButton)
        assert not window.has_unsaved_changes()

    def test_close_with_unsaved_changes(self, window, qtbot):
        """Test warning when closing with unsaved changes."""
        # Make changes
        window.typing_speed_spin.setValue(200)

        # Try to close
        with patch("PyQt6.QtWidgets.QMessageBox.question") as mock_question:
            mock_question.return_value = False  # Don't close
            window.close()
            assert window.isVisible() is True

            mock_question.return_value = True  # Do close
            window.close()
            assert window.isVisible() is False

    def test_keyboard_shortcuts(self, window, qtbot):
        """Test keyboard shortcuts work."""
        # Ctrl+S to save
        qtbot.keyClick(window, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        # Should trigger save (if changes made)

        # Escape to cancel
        qtbot.keyClick(window, Qt.Key.Key_Escape)
        # Should close window

    def test_tab_order(self, window):
        """Test tab order is logical."""
        # Performance tab should be first
        assert window.tab_widget.currentIndex() == 0
        assert window.tab_widget.tabText(0) == "Performance"
        assert window.tab_widget.tabText(1) == "History"
        assert window.tab_widget.tabText(2) == "General"
        assert window.tab_widget.tabText(3) == "Privacy"
        assert window.tab_widget.tabText(4) == "Hotkeys"

    def test_tooltips(self, window):
        """Test helpful tooltips are present."""
        assert window.typing_speed_spin.toolTip() != ""
        assert window.adaptive_delay_checkbox.toolTip() != ""
        assert window.privacy_mode_checkbox.toolTip() != ""
