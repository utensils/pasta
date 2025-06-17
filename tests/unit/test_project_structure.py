"""Test basic project structure and imports."""


class TestProjectStructure:
    """Test that the project structure is correctly set up."""

    def test_core_modules_importable(self):
        """Test that core modules can be imported."""
        from pasta.core import clipboard, hotkeys, keyboard, storage

        assert hasattr(clipboard, "ClipboardManager")
        assert hasattr(keyboard, "PastaKeyboardEngine")
        assert hasattr(storage, "StorageManager")
        assert hasattr(hotkeys, "HotkeyManager")

    def test_gui_modules_importable(self):
        """Test that GUI modules can be imported."""
        from pasta.gui import history, settings, tray

        assert hasattr(tray, "SystemTray")
        assert hasattr(settings, "SettingsWindow")
        assert hasattr(history, "HistoryWindow")

    def test_utils_modules_importable(self):
        """Test that utility modules can be imported."""
        from pasta.utils import permissions, platform, security

        assert hasattr(platform, "get_platform")
        assert hasattr(permissions, "PermissionChecker")
        assert hasattr(security, "SecurityManager")

    def test_main_entry_point_exists(self):
        """Test that the main entry point exists."""
        from pasta import __main__

        assert hasattr(__main__, "main")
