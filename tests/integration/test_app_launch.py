"""Integration tests for app launch and initialization."""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestAppLaunch:
    """Test cases for app launch and initialization."""

    @pytest.fixture(autouse=True)
    def setup(self, cleanup_pasta_processes):
        """Ensure no Pasta processes are running before each test."""
        # The cleanup_pasta_processes fixture handles killing processes
        pass

    def test_components_can_initialize(self):
        """Test that all components can be initialized without crashing."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.hotkeys import HotkeyManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.settings import SettingsManager
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # Create all components
        clipboard_manager = ClipboardManager()
        keyboard_engine = PastaKeyboardEngine()
        storage_manager = StorageManager(":memory:")
        permission_checker = PermissionChecker()
        settings_manager = SettingsManager()
        hotkey_manager = HotkeyManager()

        # Basic assertions to ensure they initialized
        assert clipboard_manager is not None
        assert keyboard_engine is not None
        assert storage_manager is not None
        assert permission_checker is not None
        assert settings_manager is not None
        assert hotkey_manager is not None

    def test_system_tray_can_initialize(self):
        """Test that SystemTray can be initialized without crashing."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.settings import SettingsManager
        from pasta.core.storage import StorageManager
        from pasta.gui.tray import SystemTray
        from pasta.utils.permissions import PermissionChecker

        # Create components
        clipboard_manager = ClipboardManager()
        keyboard_engine = PastaKeyboardEngine()
        storage_manager = StorageManager(":memory:")
        permission_checker = PermissionChecker()
        settings_manager = SettingsManager()

        # Create system tray
        tray = SystemTray(
            clipboard_manager=clipboard_manager,
            keyboard_engine=keyboard_engine,
            storage_manager=storage_manager,
            permission_checker=permission_checker,
            settings_manager=settings_manager,
        )

        assert tray is not None
        assert hasattr(tray, "tray_icon")

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific regression test")
    def test_macos_no_corefoundation_crash(self):
        """Regression test: Ensure no CoreFoundation crash on macOS initialization."""
        from pasta.core.hotkeys import KEYBOARD_AVAILABLE, HotkeyManager

        # Verify keyboard module is disabled on macOS
        assert not KEYBOARD_AVAILABLE

        # Create hotkey manager - should not crash
        hotkey_manager = HotkeyManager()
        hotkey_manager.register_hotkeys()
        hotkey_manager.unregister_hotkeys()

    def test_clipboard_monitoring_lifecycle(self):
        """Test clipboard monitoring can start and stop without issues."""
        from pasta.core.clipboard import ClipboardManager

        manager = ClipboardManager()

        # Start monitoring
        manager.start_monitoring()
        assert manager.monitoring

        # Give it a moment to ensure thread starts
        time.sleep(0.1)

        # Stop monitoring
        manager.stop_monitoring()
        assert not manager.monitoring

    def test_settings_manager_lifecycle(self):
        """Test settings manager can load and save without issues."""
        # Create with temp file
        import tempfile

        from pasta.core.settings import SettingsManager

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            settings_path = tmp.name

        try:
            manager = SettingsManager(settings_path=settings_path)

            # Test load (should handle missing file)
            manager.load()

            # Modify settings
            manager.settings.typing_speed = 150

            # Test save
            manager.save()

            # Verify file was created
            assert Path(settings_path).exists()

            # Test loading saved settings
            new_manager = SettingsManager(settings_path=settings_path)
            new_manager.load()
            assert new_manager.settings.typing_speed == 150

        finally:
            # Cleanup
            Path(settings_path).unlink(missing_ok=True)

    def test_concurrent_component_initialization(self):
        """Test that components can be initialized concurrently without issues."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.hotkeys import HotkeyManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.settings import SettingsManager
        from pasta.core.storage import StorageManager

        components = {}
        errors = []

        def create_component(name, factory):
            try:
                components[name] = factory()
            except Exception as e:
                errors.append((name, e))

        # Create components in parallel
        threads = [
            threading.Thread(target=create_component, args=("clipboard", ClipboardManager)),
            threading.Thread(target=create_component, args=("keyboard", PastaKeyboardEngine)),
            threading.Thread(target=create_component, args=("storage", lambda: StorageManager(":memory:"))),
            threading.Thread(target=create_component, args=("settings", SettingsManager)),
            threading.Thread(target=create_component, args=("hotkeys", HotkeyManager)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check for errors
        assert len(errors) == 0, f"Errors during initialization: {errors}"
        assert len(components) == 5

    @pytest.mark.skip(reason="Causes issues in CI - process gets terminated")
    def test_app_startup_sequence(self):
        """Test the full app startup sequence (without actually running the GUI)."""
        import contextlib

        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray.SystemTray.run"),
            patch("pasta.utils.permissions.PermissionChecker.check_permissions", return_value=True),
            patch("sys.exit"),
        ):
            # Import and test main initialization
            from pasta.__main__ import main

            # This should not crash
            with contextlib.suppress(KeyboardInterrupt):
                main()
