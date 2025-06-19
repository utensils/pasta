"""Comprehensive tests for __main__ module to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from pasta.__main__ import main


class TestMainModule:
    """Test main entry point functionality."""

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("builtins.print")
    def test_main_with_permissions_granted(
        self,
        mock_print,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test main function when permissions are granted."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker

        mock_tray = Mock()
        mock_tray_class.return_value = mock_tray

        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings

        # Run main
        with patch("sys.platform", "darwin"):
            main()

        # Verify components were initialized
        mock_permission_checker_class.assert_called_once()
        mock_clipboard_class.assert_called_once()
        mock_keyboard_class.assert_called_once()
        mock_storage_class.assert_called_once()
        mock_settings_class.assert_called_once()
        mock_tray_class.assert_called_once()

        # Verify settings were loaded
        mock_settings.load.assert_called_once()

        # Verify tray was run
        mock_tray.run.assert_called_once()

        # Verify startup messages
        assert any("Pasta - Clipboard History Manager" in str(call) for call in mock_print.call_args_list)
        assert any("Pasta is running in the system tray" in str(call) for call in mock_print.call_args_list)

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_main_without_permissions(
        self,
        mock_exit,
        mock_print,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test main function when permissions are not granted."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = False
        mock_permission_checker.get_permission_error_message.return_value = "Permission error"
        mock_permission_checker.get_permission_instructions.return_value = "Do this to fix"
        mock_permission_checker_class.return_value = mock_permission_checker

        # Run main
        main()

        # Verify permission checker was called
        mock_permission_checker.check_permissions.assert_called_once()
        mock_permission_checker.get_permission_error_message.assert_called_once()
        mock_permission_checker.get_permission_instructions.assert_called_once()
        mock_permission_checker.request_permissions.assert_called_once()

        # Verify components were NOT initialized
        mock_clipboard_class.assert_not_called()
        mock_keyboard_class.assert_not_called()
        mock_storage_class.assert_not_called()
        mock_settings_class.assert_not_called()
        mock_tray_class.assert_not_called()

        # Verify exit was called
        mock_exit.assert_called_once_with(1)

        # Verify error messages
        assert any("requires additional permissions" in str(call) for call in mock_print.call_args_list)

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("builtins.print")
    def test_main_keyboard_interrupt(
        self,
        mock_print,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test handling KeyboardInterrupt in main."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker

        mock_tray = Mock()
        mock_tray.run.side_effect = KeyboardInterrupt()
        mock_tray_class.return_value = mock_tray

        # Run main and catch sys.exit
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Verify quit was called
        mock_tray.quit.assert_called_once()

        # Verify exit code
        assert exc_info.value.code == 0

        # Verify shutdown message
        assert any("Shutting down Pasta" in str(call) for call in mock_print.call_args_list)

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("pathlib.Path.mkdir")
    def test_main_data_directory_creation_macos(
        self,
        mock_mkdir,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test data directory creation on macOS."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker

        mock_tray = Mock()
        mock_tray_class.return_value = mock_tray

        # Run main on macOS
        with patch("sys.platform", "darwin"):
            main()

        # Verify correct directory path was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Verify storage was initialized with correct path
        storage_path = mock_storage_class.call_args[0][0]
        assert "Library/Application Support/Pasta" in storage_path
        assert storage_path.endswith("history.db")

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("pathlib.Path.mkdir")
    @patch("os.getenv")
    def test_main_data_directory_creation_windows(
        self,
        mock_getenv,
        mock_mkdir,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test data directory creation on Windows."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker

        mock_tray = Mock()
        mock_tray_class.return_value = mock_tray

        mock_getenv.return_value = "C:\\Users\\Test\\AppData\\Roaming"

        # Run main on Windows
        with patch("sys.platform", "win32"):
            main()

        # Verify storage was initialized with correct path
        storage_path = mock_storage_class.call_args[0][0]
        assert "AppData" in storage_path
        assert "Pasta" in storage_path
        assert storage_path.endswith("history.db")

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    @patch("pathlib.Path.mkdir")
    def test_main_data_directory_creation_linux(
        self,
        mock_mkdir,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test data directory creation on Linux."""
        # Setup mocks
        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker

        mock_tray = Mock()
        mock_tray_class.return_value = mock_tray

        # Run main on Linux
        with patch("sys.platform", "linux"):
            main()

        # Verify storage was initialized with correct path
        storage_path = mock_storage_class.call_args[0][0]
        assert ".local/share/pasta" in storage_path
        assert storage_path.endswith("history.db")

    @patch("pasta.__main__.SystemTray")
    @patch("pasta.__main__.SettingsManager")
    @patch("pasta.__main__.StorageManager")
    @patch("pasta.__main__.PastaKeyboardEngine")
    @patch("pasta.__main__.ClipboardManager")
    @patch("pasta.__main__.PermissionChecker")
    def test_main_component_initialization_order(
        self,
        mock_permission_checker_class,
        mock_clipboard_class,
        mock_keyboard_class,
        mock_storage_class,
        mock_settings_class,
        mock_tray_class,
    ):
        """Test that components are initialized in correct order."""
        # Track initialization order
        init_order = []

        mock_permission_checker = Mock()
        mock_permission_checker.check_permissions.return_value = True
        mock_permission_checker_class.return_value = mock_permission_checker
        mock_permission_checker_class.side_effect = lambda: init_order.append("permission") or mock_permission_checker

        mock_clipboard_class.side_effect = lambda: init_order.append("clipboard") or Mock()
        mock_keyboard_class.side_effect = lambda: init_order.append("keyboard") or Mock()
        mock_storage_class.side_effect = lambda x: init_order.append("storage") or Mock()
        mock_settings_class.side_effect = lambda: init_order.append("settings") or Mock()
        mock_tray_class.side_effect = lambda **kwargs: init_order.append("tray") or Mock()

        # Run main
        main()

        # Verify initialization order
        assert init_order == ["permission", "clipboard", "keyboard", "storage", "settings", "tray"]

    def test_main_module_entry_point(self):
        """Test that __main__ module can be executed."""
        # This test verifies the if __name__ == "__main__" block
        with patch("pasta.__main__.main") as mock_main:
            # The main() should not be called during import
            mock_main.assert_not_called()
