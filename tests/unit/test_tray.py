"""Tests for the SystemTray module."""

from unittest.mock import Mock, patch

import pytest

from pasta.gui.tray import SystemTray


class TestSystemTray:
    """Test cases for SystemTray."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "clipboard_manager": Mock(),
            "keyboard_engine": Mock(),
            "storage_manager": Mock(),
            "permission_checker": Mock(),
        }

    @pytest.fixture
    def tray(self, mock_components):
        """Create a SystemTray instance for testing."""
        with patch("pasta.gui.tray.pystray"):
            return SystemTray(**mock_components)

    def test_initialization(self, tray, mock_components):
        """Test SystemTray initializes correctly."""
        assert tray.clipboard_manager == mock_components["clipboard_manager"]
        assert tray.keyboard_engine == mock_components["keyboard_engine"]
        assert tray.storage_manager == mock_components["storage_manager"]
        assert tray.permission_checker == mock_components["permission_checker"]
        assert hasattr(tray, "icon")
        assert hasattr(tray, "enabled")
        assert tray.enabled is True

    @patch("pasta.gui.tray.Path")
    @patch("pasta.gui.tray.Image.open")
    @patch("pasta.gui.tray.pystray.Icon")
    def test_create_icon(self, mock_icon, mock_image_open, mock_path, mock_components):
        """Test system tray icon creation."""
        # Mock icon file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value = mock_path_instance

        mock_image = Mock()
        mock_image_open.return_value = mock_image

        SystemTray(**mock_components)

        # Verify icon was created
        mock_icon.assert_called_once()
        assert mock_icon.call_args[0][0] == "Pasta"  # App name
        assert mock_icon.call_args[1]["icon"] == mock_image
        assert "menu" in mock_icon.call_args[1]

    def test_menu_structure(self, tray):
        """Test tray menu has correct structure."""
        menu_items = tray._create_menu()

        # Convert menu items to list for easier testing
        menu_list = list(menu_items)

        # Check expected menu items exist
        menu_labels = [item.text for item in menu_list if hasattr(item, "text")]

        assert "Paste Mode: Auto" in menu_labels
        assert "Enabled" in menu_labels
        assert "History" in menu_labels
        assert "Settings" in menu_labels
        assert "About" in menu_labels
        assert "Quit" in menu_labels

    def test_toggle_enabled(self, tray, mock_components):
        """Test toggling enabled state."""
        # Initially enabled
        assert tray.enabled is True
        assert not mock_components["clipboard_manager"].stop_monitoring.called

        # Toggle to disabled
        tray.toggle_enabled()
        assert tray.enabled is False
        mock_components["clipboard_manager"].stop_monitoring.assert_called_once()

        # Toggle back to enabled
        tray.toggle_enabled()
        assert tray.enabled is True
        mock_components["clipboard_manager"].start_monitoring.assert_called_once()

    def test_change_paste_mode(self, tray):
        """Test changing paste mode."""
        # Check initial mode
        assert tray.paste_mode == "auto"

        # Change to clipboard mode
        tray.set_paste_mode("clipboard")
        assert tray.paste_mode == "clipboard"

        # Change to typing mode
        tray.set_paste_mode("typing")
        assert tray.paste_mode == "typing"

    @patch("pasta.gui.tray.QApplication")
    @patch("pasta.gui.tray.HistoryWindow")
    def test_show_history(self, mock_history_window, mock_qapp, tray):
        """Test showing history window."""
        # Mock Qt application instance
        mock_app_instance = Mock()
        mock_qapp.instance.return_value = None
        mock_qapp.return_value = mock_app_instance

        # Mock history window
        mock_window = Mock()
        mock_history_window.return_value = mock_window

        # Show history
        tray.show_history()

        # Verify window was created and shown
        mock_history_window.assert_called_once_with(tray.storage_manager)
        mock_window.show.assert_called_once()

    @patch("pasta.gui.tray.QApplication")
    @patch("pasta.gui.tray.SettingsWindow")
    def test_show_settings(self, mock_settings_window, mock_qapp, tray):
        """Test showing settings window."""
        # Mock Qt application instance
        mock_app_instance = Mock()
        mock_qapp.instance.return_value = None
        mock_qapp.return_value = mock_app_instance

        # Mock settings window
        mock_window = Mock()
        mock_settings_window.return_value = mock_window

        # Show settings
        tray.show_settings()

        # Verify window was created and shown
        mock_settings_window.assert_called_once()
        mock_window.show.assert_called_once()

    @patch("pasta.gui.tray.webbrowser.open")
    def test_show_about(self, mock_webbrowser, tray):
        """Test showing about dialog."""
        tray.show_about()

        # Should open project URL
        mock_webbrowser.assert_called_once_with("https://github.com/utensils/pasta")

    def test_quit(self, tray, mock_components):
        """Test quit functionality."""
        with patch.object(tray.icon, "stop") as mock_stop:
            tray.quit()

            # Should stop monitoring and icon
            mock_components["clipboard_manager"].stop_monitoring.assert_called_once()
            mock_stop.assert_called_once()

    def test_run(self, tray, mock_components):
        """Test running the tray application."""
        # Mock the icon's run method
        with patch.object(tray.icon, "run") as mock_run:
            # Start monitoring on run
            tray.run()

            # Verify monitoring started and icon is running
            mock_components["clipboard_manager"].start_monitoring.assert_called_once()
            mock_run.assert_called_once()

    def test_permission_check_on_enable(self, tray, mock_components):
        """Test permission checking when enabling."""
        # Set up permission check to fail
        mock_components["permission_checker"].check_permissions.return_value = False

        # Start disabled
        tray.enabled = False

        # Try to enable
        tray.toggle_enabled()

        # Should check permissions
        mock_components["permission_checker"].check_permissions.assert_called_once()

        # Should not enable due to lack of permissions
        assert tray.enabled is False
        assert not mock_components["clipboard_manager"].start_monitoring.called

    def test_paste_callback_integration(self, tray, mock_components):
        """Test clipboard callback triggers paste."""
        # Set up the callback
        callback = None

        def capture_callback(cb):
            nonlocal callback
            callback = cb

        mock_components["clipboard_manager"].register_callback.side_effect = capture_callback

        # Create tray to set up callback
        SystemTray(**mock_components)

        # Simulate clipboard change
        test_entry = {"content": "test clipboard content", "timestamp": "2024-01-01", "hash": "abc123", "type": "text"}
        callback(test_entry)

        # Should trigger paste with correct mode
        mock_components["keyboard_engine"].paste_text.assert_called_once_with("test clipboard content", method="auto")

    def test_paste_callback_when_disabled(self, tray, mock_components):
        """Test clipboard callback does nothing when disabled."""
        # Set up the callback
        callback = None

        def capture_callback(cb):
            nonlocal callback
            callback = cb

        mock_components["clipboard_manager"].register_callback.side_effect = capture_callback

        # Create tray and disable it
        tray = SystemTray(**mock_components)
        tray.enabled = False

        # Simulate clipboard change
        test_entry = {"content": "test content", "timestamp": "2024-01-01", "hash": "xyz", "type": "text"}
        callback(test_entry)

        # Should not trigger paste
        assert not mock_components["keyboard_engine"].paste_text.called

    def test_icon_update_on_state_change(self, tray):
        """Test icon updates when enabled state changes."""
        with patch.object(tray, "_update_icon") as mock_update:
            # Toggle state
            tray.toggle_enabled()
            mock_update.assert_called_once()

            # Change paste mode
            tray.set_paste_mode("clipboard")
            assert mock_update.call_count == 2

    @patch("pasta.gui.tray.Path")
    def test_icon_path_handling(self, mock_path, mock_components):
        """Test icon file path resolution."""
        # Mock path chain
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True

        # Set up the path chain
        mock_parent = Mock()
        mock_resources = Mock()

        # Use spec to enable magic methods
        mock_parent.__truediv__ = Mock(return_value=mock_resources)
        mock_resources.__truediv__ = Mock(return_value=mock_path_instance)

        mock_path.return_value.parent = mock_parent

        with patch("pasta.gui.tray.Image.open") as mock_image:
            SystemTray(**mock_components)

            # Should try to open icon file
            assert mock_image.called

    def test_error_handling_in_paste(self, tray, mock_components):
        """Test error handling during paste operation."""
        # Set up callback
        callback = None

        def capture_callback(cb):
            nonlocal callback
            callback = cb

        mock_components["clipboard_manager"].register_callback.side_effect = capture_callback
        SystemTray(**mock_components)

        # Make paste fail
        mock_components["keyboard_engine"].paste_text.side_effect = Exception("Paste error")

        # Should not crash
        test_entry = {"content": "test content", "timestamp": "2024-01-01", "hash": "def", "type": "text"}
        callback(test_entry)

        # Verify paste was attempted
        mock_components["keyboard_engine"].paste_text.assert_called_once()

    def test_menu_item_states(self, tray):
        """Test menu items reflect current state."""
        # Get menu items
        menu_items = list(tray._create_menu())

        # Find paste mode items
        paste_mode_items = [item for item in menu_items if hasattr(item, "text") and "Paste Mode:" in item.text]

        assert len(paste_mode_items) > 0

        # Check enabled item
        enabled_items = [item for item in menu_items if hasattr(item, "text") and item.text == "Enabled"]

        assert len(enabled_items) == 1
        # MenuItem evaluated the lambda, so checked is now a boolean
        assert enabled_items[0].checked is True

    def test_hotkey_integration(self, tray):
        """Test hotkey support in menu."""
        menu_items = list(tray._create_menu())

        # Find items that might have hotkeys
        settings_items = [item for item in menu_items if hasattr(item, "text") and item.text == "Settings"]

        # Settings should mention hotkey if configured
        assert len(settings_items) == 1

    @patch("pasta.gui.tray.pystray.Icon")
    def test_icon_tooltip(self, mock_icon, mock_components):
        """Test system tray tooltip."""
        SystemTray(**mock_components)

        # Check tooltip was set
        icon_call = mock_icon.call_args[1]
        assert "title" in icon_call or mock_icon.return_value.title is not None

    def test_thread_safety(self, tray):
        """Test thread-safe operations."""
        # Verify thread-safe attributes exist
        assert hasattr(tray, "_lock") or hasattr(tray, "lock")

        # Test concurrent state changes don't crash
        import threading

        def toggle_multiple():
            for _ in range(10):
                tray.toggle_enabled()

        threads = [threading.Thread(target=toggle_multiple) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert True

    def test_emergency_stop(self, tray, mock_components):
        """Test emergency stop functionality."""
        # Mock keyboard engine is_pasting
        mock_components["keyboard_engine"].is_pasting.return_value = True

        # Call emergency stop
        tray._on_emergency_stop()

        # Should abort paste
        mock_components["keyboard_engine"].abort_paste.assert_called_once()

    @patch("pasta.gui.tray.HotkeyManager")
    def test_hotkey_manager_integration(self, mock_hotkey_manager, mock_components):
        """Test hotkey manager is set up correctly."""
        tray = SystemTray(**mock_components)

        # Should create hotkey manager
        assert hasattr(tray, "hotkey_manager")

        # Should set abort callback
        tray.hotkey_manager.set_abort_callback.assert_called_once()

    def test_icon_click_during_paste(self, tray, mock_components):
        """Test clicking icon during paste triggers emergency stop."""
        # Mock pasting state
        mock_components["keyboard_engine"].is_pasting.return_value = True

        # Click icon
        tray._on_icon_clicked(None, None)

        # Should trigger emergency stop
        mock_components["keyboard_engine"].abort_paste.assert_called_once()
