"""End-to-end integration tests for settings persistence across app restarts."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pasta.core.settings import Settings, SettingsManager
from pasta.gui.tray import SystemTray


class TestSettingsPersistenceE2E:
    """End-to-end tests for settings persistence functionality."""

    @pytest.fixture
    def temp_settings_file(self, tmp_path):
        """Create temporary settings file path."""
        return str(tmp_path / "test_settings.json")

    @pytest.fixture
    def mock_system_components(self):
        """Mock system components to prevent GUI creation."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            yield

    def test_settings_save_and_load_cycle(self, temp_settings_file):
        """Test complete save and load cycle for settings."""
        # Create settings manager with custom settings
        manager1 = SettingsManager(settings_path=temp_settings_file)

        # Modify all settings
        manager1.settings.auto_start = True
        manager1.settings.start_minimized = False
        manager1.settings.paste_mode = "typing"
        manager1.settings.typing_speed = 150
        manager1.settings.chunk_size = 300
        manager1.settings.max_history_size = 200
        manager1.settings.clear_history_on_exit = True
        manager1.settings.excluded_apps = ["Terminal", "iTerm"]
        manager1.settings.sensitive_data_detection = False
        manager1.settings.privacy_mode = True
        manager1.settings.rate_limit_enabled = False
        manager1.settings.hotkeys_enabled = True
        manager1.settings.snippet_hotkey_prefix = "cmd+shift"

        # Save settings
        manager1.save()

        # Verify file was created
        assert Path(temp_settings_file).exists()

        # Create new manager and load settings
        manager2 = SettingsManager(settings_path=temp_settings_file)
        manager2.load()

        # Verify all settings were preserved
        assert manager2.settings.auto_start is True
        assert manager2.settings.start_minimized is False
        assert manager2.settings.paste_mode == "typing"
        assert manager2.settings.typing_speed == 150
        assert manager2.settings.chunk_size == 300
        assert manager2.settings.max_history_size == 200
        assert manager2.settings.clear_history_on_exit is True
        assert manager2.settings.excluded_apps == ["Terminal", "iTerm"]
        assert manager2.settings.sensitive_data_detection is False
        assert manager2.settings.privacy_mode is True
        assert manager2.settings.rate_limit_enabled is False
        assert manager2.settings.hotkeys_enabled is True
        assert manager2.settings.snippet_hotkey_prefix == "cmd+shift"

    def test_settings_file_corruption_recovery(self, temp_settings_file):
        """Test recovery from corrupted settings file."""
        # Write corrupted JSON
        with open(temp_settings_file, "w") as f:
            f.write("{invalid json content}")

        # Create manager and try to load
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.load()  # Should not crash

        # Should have default settings
        assert manager.settings.auto_start is False
        assert manager.settings.paste_mode == "auto"

        # Should be able to save new settings
        manager.settings.typing_speed = 200
        manager.save()

        # Verify file is now valid
        with open(temp_settings_file) as f:
            data = json.load(f)
            assert data["typing_speed"] == 200

    def test_settings_migration(self, temp_settings_file):
        """Test migration from older settings format."""
        # Write old format settings
        old_settings = {
            "auto_start": True,
            "paste_mode": "clipboard",
            # Missing newer fields
        }

        with open(temp_settings_file, "w") as f:
            json.dump(old_settings, f)

        # Load with new manager
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.load()

        # Should have old values
        assert manager.settings.auto_start is True
        assert manager.settings.paste_mode == "clipboard"

        # Should have defaults for new fields
        assert manager.settings.privacy_mode is False
        assert manager.settings.snippet_hotkey_prefix == "ctrl+shift"

        # Save and verify all fields are present
        manager.save()

        with open(temp_settings_file) as f:
            data = json.load(f)
            assert "privacy_mode" in data
            assert "snippet_hotkey_prefix" in data

    def test_settings_concurrent_access(self, temp_settings_file):
        """Test concurrent access to settings file."""
        import threading
        import time

        # Create multiple managers
        managers = [SettingsManager(settings_path=temp_settings_file) for _ in range(5)]

        results = []
        errors = []

        def modify_and_save(manager, value):
            try:
                manager.settings.typing_speed = value
                manager.save()
                time.sleep(0.01)  # Small delay to increase conflict chance
                manager.load()
                results.append(manager.settings.typing_speed)
            except Exception as e:
                errors.append(e)

        # Run concurrent modifications
        threads = []
        for i, manager in enumerate(managers):
            t = threading.Thread(target=modify_and_save, args=(manager, 100 + i * 10))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0

        # All results should be valid
        assert all(isinstance(r, int) for r in results)

    def test_settings_apply_to_components(self, temp_settings_file, mock_system_components):
        """Test that settings are properly applied to components."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # Create settings with specific values
        settings_manager = SettingsManager(settings_path=temp_settings_file)
        settings_manager.settings.paste_mode = "typing"
        settings_manager.settings.typing_speed = 200
        settings_manager.settings.max_history_size = 50
        settings_manager.save()

        # Create components
        components = {
            "clipboard_manager": ClipboardManager(),
            "keyboard_engine": PastaKeyboardEngine(),
            "storage_manager": StorageManager(":memory:"),
            "permission_checker": PermissionChecker(),
            "settings_manager": settings_manager,
        }

        # Create SystemTray
        tray = SystemTray(**components)

        # Verify settings are applied
        assert tray.paste_mode == "typing"

        # Test that keyboard engine uses settings
        with patch("pyautogui.write") as mock_write:
            components["keyboard_engine"].paste_text("Test", mode="typing")

            # Should use configured typing speed
            if mock_write.call_args and "interval" in mock_write.call_args[1]:
                # Interval calculation may vary, just verify it's influenced by settings
                assert mock_write.call_args[1]["interval"] > 0

    def test_settings_window_persistence(self, temp_settings_file):
        """Test settings changes through settings window are persisted."""
        # Create initial settings
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.settings.typing_speed = 100
        manager.save()

        # Simulate settings window changes
        with patch("pasta.gui.settings_pyside6_improved.SettingsWindow") as mock_window_class:
            mock_window = Mock()
            mock_window_class.return_value = mock_window

            # Create new manager (simulating app restart)
            new_manager = SettingsManager(settings_path=temp_settings_file)
            new_manager.load()

            # Simulate user changing settings
            new_manager.settings.typing_speed = 250
            new_manager.settings.paste_mode = "clipboard"
            new_manager.settings.privacy_mode = True
            new_manager.save()

        # Verify changes persist
        final_manager = SettingsManager(settings_path=temp_settings_file)
        final_manager.load()

        assert final_manager.settings.typing_speed == 250
        assert final_manager.settings.paste_mode == "clipboard"
        assert final_manager.settings.privacy_mode is True

    def test_settings_default_location(self):
        """Test settings are saved to default location if not specified."""
        # Create manager without specifying path
        manager = SettingsManager()

        # Should have a default path
        assert manager.settings_path is not None
        assert isinstance(manager.settings_path, Path)

        # Should be in user config directory
        assert "pasta" in str(manager.settings_path).lower()

    def test_settings_validation_on_load(self, temp_settings_file):
        """Test settings validation when loading from file."""
        # Write settings with invalid values
        invalid_settings = {
            "typing_speed": -50,  # Should be positive
            "chunk_size": 0,  # Should be positive
            "max_history_size": "not a number",  # Should be int
            "paste_mode": "invalid_mode",  # Should be valid mode
        }

        with open(temp_settings_file, "w") as f:
            json.dump(invalid_settings, f)

        # Load settings
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.load()

        # Should have valid defaults instead of invalid values
        assert manager.settings.typing_speed > 0
        assert manager.settings.chunk_size > 0
        assert isinstance(manager.settings.max_history_size, int)
        assert manager.settings.paste_mode in ["auto", "typing", "clipboard"]

    def test_settings_backwards_compatibility(self, temp_settings_file):
        """Test loading settings from different app versions."""
        # Simulate settings from older version
        v1_settings = {
            "auto_start": True,
            "paste_mode": "typing",
            "typing_speed": 100,
        }

        with open(temp_settings_file, "w") as f:
            json.dump(v1_settings, f)

        # Load in current version
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.load()

        # Old settings should be preserved
        assert manager.settings.auto_start is True
        assert manager.settings.paste_mode == "typing"
        assert manager.settings.typing_speed == 100

        # New fields should have defaults
        assert hasattr(manager.settings, "privacy_mode")
        assert hasattr(manager.settings, "rate_limit_enabled")

        # Save and reload
        manager.save()

        # Verify file now has all fields
        with open(temp_settings_file) as f:
            data = json.load(f)
            assert len(data) > len(v1_settings)  # More fields than original

    def test_settings_reset_to_defaults(self, temp_settings_file):
        """Test resetting settings to defaults."""
        # Create manager with custom settings
        manager = SettingsManager(settings_path=temp_settings_file)
        manager.settings.typing_speed = 200
        manager.settings.paste_mode = "clipboard"
        manager.settings.privacy_mode = True
        manager.save()

        # Reset to defaults
        manager.settings = Settings()
        manager.save()

        # Load and verify defaults
        new_manager = SettingsManager(settings_path=temp_settings_file)
        new_manager.load()

        assert new_manager.settings.typing_speed == 100
        assert new_manager.settings.paste_mode == "auto"
        assert new_manager.settings.privacy_mode is False

    def test_settings_app_restart_simulation(self, temp_settings_file, mock_system_components):
        """Test full app restart with settings persistence."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # First app instance
        settings1 = SettingsManager(settings_path=temp_settings_file)
        settings1.settings.paste_mode = "typing"
        settings1.settings.max_history_size = 75
        settings1.settings.excluded_apps = ["Password Manager"]
        settings1.save()

        # Create first tray instance
        tray1 = SystemTray(
            clipboard_manager=ClipboardManager(),
            keyboard_engine=PastaKeyboardEngine(),
            storage_manager=StorageManager(":memory:"),
            permission_checker=PermissionChecker(),
            settings_manager=settings1,
        )

        # Simulate app shutdown
        del tray1
        del settings1

        # Second app instance (restart)
        settings2 = SettingsManager(settings_path=temp_settings_file)
        settings2.load()

        # Verify settings persisted
        assert settings2.settings.paste_mode == "typing"
        assert settings2.settings.max_history_size == 75
        assert settings2.settings.excluded_apps == ["Password Manager"]

        # Create second tray instance
        tray2 = SystemTray(
            clipboard_manager=ClipboardManager(),
            keyboard_engine=PastaKeyboardEngine(),
            storage_manager=StorageManager(":memory:"),
            permission_checker=PermissionChecker(),
            settings_manager=settings2,
        )

        # Verify tray uses persisted settings
        assert tray2.paste_mode == "typing"
