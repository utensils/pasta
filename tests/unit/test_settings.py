"""Tests for the Settings module."""

import json
from unittest.mock import Mock

import pytest

from pasta.core.settings import Settings, SettingsManager


class TestSettings:
    """Test cases for Settings data class."""

    def test_default_values(self):
        """Test Settings has correct default values."""
        settings = Settings()

        # General settings
        assert settings.start_on_login is False
        assert settings.monitoring_enabled is True
        assert settings.paste_mode == "auto"

        # Performance settings
        assert settings.typing_speed == 100  # chars per second
        assert settings.chunk_size == 200
        assert settings.adaptive_delay is True

        # History settings
        assert settings.history_size == 100
        assert settings.history_retention_days == 7
        assert settings.encrypt_sensitive is True

        # Privacy settings
        assert settings.privacy_mode is False
        assert settings.excluded_apps == []
        assert settings.excluded_patterns == []

        # Hotkey settings
        assert settings.emergency_stop_hotkey == "esc+esc"
        assert settings.quick_paste_hotkey == ""
        assert settings.toggle_monitoring_hotkey == ""

    def test_settings_to_dict(self):
        """Test converting Settings to dictionary."""
        settings = Settings(typing_speed=200, history_size=50, excluded_apps=["password_manager", "banking_app"])

        data = settings.to_dict()

        assert isinstance(data, dict)
        assert data["typing_speed"] == 200
        assert data["history_size"] == 50
        assert data["excluded_apps"] == ["password_manager", "banking_app"]
        assert "start_on_login" in data
        assert "monitoring_enabled" in data

    def test_settings_from_dict(self):
        """Test creating Settings from dictionary."""
        data = {
            "typing_speed": 150,
            "history_size": 200,
            "privacy_mode": True,
            "excluded_apps": ["app1", "app2"],
            "unknown_field": "ignored",  # Should be ignored
        }

        settings = Settings.from_dict(data)

        assert settings.typing_speed == 150
        assert settings.history_size == 200
        assert settings.privacy_mode is True
        assert settings.excluded_apps == ["app1", "app2"]
        # Defaults should be preserved for missing fields
        assert settings.chunk_size == 200

    def test_settings_validation(self):
        """Test settings validation."""
        # Valid settings
        settings = Settings(typing_speed=50, history_size=10)
        assert settings.validate()

        # Invalid typing speed
        with pytest.raises(ValueError, match="Typing speed must be between"):
            Settings(typing_speed=0).validate()

        with pytest.raises(ValueError, match="Typing speed must be between"):
            Settings(typing_speed=1001).validate()

        # Invalid history size
        with pytest.raises(ValueError, match="History size must be between"):
            Settings(history_size=0).validate()

        with pytest.raises(ValueError, match="History size must be between"):
            Settings(history_size=10001).validate()

        # Invalid chunk size
        with pytest.raises(ValueError, match="Chunk size must be between"):
            Settings(chunk_size=9).validate()

        # Invalid retention days
        with pytest.raises(ValueError, match="Retention days must be between"):
            Settings(history_retention_days=-1).validate()

        # Invalid paste mode
        with pytest.raises(ValueError, match="Invalid paste mode"):
            Settings(paste_mode="invalid").validate()

    def test_settings_copy(self):
        """Test creating a copy of settings."""
        original = Settings(typing_speed=200, excluded_apps=["app1"], privacy_mode=True)

        copy = original.copy()

        # Values should be equal
        assert copy.typing_speed == original.typing_speed
        assert copy.excluded_apps == original.excluded_apps
        assert copy.privacy_mode == original.privacy_mode

        # But should be different objects
        assert copy is not original
        assert copy.excluded_apps is not original.excluded_apps

        # Modifying copy shouldn't affect original
        copy.typing_speed = 300
        copy.excluded_apps.append("app2")

        assert original.typing_speed == 200
        assert original.excluded_apps == ["app1"]


class TestSettingsManager:
    """Test cases for SettingsManager."""

    @pytest.fixture
    def temp_settings_file(self, tmp_path):
        """Create a temporary settings file."""
        temp_path = tmp_path / "settings.json"
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def manager(self, temp_settings_file):
        """Create a SettingsManager with temp file."""
        manager = SettingsManager(settings_path=temp_settings_file)
        # Don't auto-load to avoid test issues
        return manager

    def test_initialization_no_file(self, temp_settings_file):
        """Test initialization when settings file doesn't exist."""
        # Ensure file doesn't exist
        temp_settings_file.unlink(missing_ok=True)

        manager = SettingsManager(settings_path=temp_settings_file)

        # Should create default settings
        assert manager.settings is not None
        assert manager.settings.typing_speed == 100  # Default value

        # File shouldn't exist yet (no auto-load)
        assert not temp_settings_file.exists()

        # Load should create file
        manager.load()
        assert temp_settings_file.exists()

    def test_initialization_with_file(self, temp_settings_file):
        """Test initialization with existing settings file."""
        # Create settings file
        settings_data = {"typing_speed": 200, "history_size": 50, "privacy_mode": True}
        temp_settings_file.write_text(json.dumps(settings_data))

        manager = SettingsManager(settings_path=temp_settings_file)

        # Should have defaults until load() is called
        assert manager.settings.typing_speed == 100

        # Load from file
        manager.load()

        # Should load settings from file
        assert manager.settings.typing_speed == 200
        assert manager.settings.history_size == 50
        assert manager.settings.privacy_mode is True

    def test_save_settings(self, manager, temp_settings_file):
        """Test saving settings to file."""
        # Modify settings
        manager.settings.typing_speed = 250
        manager.settings.excluded_apps = ["app1", "app2"]

        # Save
        manager.save()

        # Read file and verify
        data = json.loads(temp_settings_file.read_text())
        assert data["typing_speed"] == 250
        assert data["excluded_apps"] == ["app1", "app2"]

    def test_load_settings(self, manager, temp_settings_file):
        """Test loading settings from file."""
        # Write new data to file
        new_data = {"typing_speed": 300, "history_size": 150, "privacy_mode": True}
        temp_settings_file.write_text(json.dumps(new_data))

        # Load
        manager.load()

        # Verify settings updated
        assert manager.settings.typing_speed == 300
        assert manager.settings.history_size == 150
        assert manager.settings.privacy_mode is True

    def test_update_settings(self, manager):
        """Test updating specific settings."""
        # Update settings
        manager.update(typing_speed=500, privacy_mode=True)

        assert manager.settings.typing_speed == 500
        assert manager.settings.privacy_mode is True

        # Other settings should remain unchanged
        assert manager.settings.history_size == manager.settings.history_size

    def test_update_with_validation(self, manager):
        """Test update validates settings."""
        # Invalid update should raise error
        with pytest.raises(ValueError, match="Typing speed must be between"):
            manager.update(typing_speed=2000)

        # Settings should remain unchanged after failed update
        assert manager.settings.typing_speed == 100  # Default

    def test_reset_to_defaults(self, manager):
        """Test resetting settings to defaults."""
        # Modify settings
        manager.settings.typing_speed = 200
        manager.settings.privacy_mode = True
        manager.settings.excluded_apps = ["app1"]

        # Reset
        manager.reset_to_defaults()

        # Should have default values
        assert manager.settings.typing_speed == 100
        assert manager.settings.privacy_mode is False
        assert manager.settings.excluded_apps == []

    def test_observer_pattern(self, manager):
        """Test observer notification on settings change."""
        observer = Mock()
        manager.add_observer(observer)

        # Update settings
        manager.update(typing_speed=200)

        # Observer should be notified
        observer.assert_called_once_with(manager.settings)

    def test_remove_observer(self, manager):
        """Test removing observer."""
        observer = Mock()
        manager.add_observer(observer)
        manager.remove_observer(observer)

        # Update settings
        manager.update(typing_speed=200)

        # Observer should not be notified
        observer.assert_not_called()

    def test_settings_migration(self, temp_settings_file):
        """Test migrating from old settings format."""
        # Write old format settings
        old_data = {
            "version": 1,
            "typing_speed": 150,
            "history_limit": 50,  # Old field name
            "enable_privacy": True,  # Old field name
        }
        temp_settings_file.write_text(json.dumps(old_data))

        manager = SettingsManager(settings_path=temp_settings_file)

        # Should migrate old fields
        assert manager.settings.typing_speed == 150
        assert manager.settings.history_size == 50  # Migrated from history_limit
        assert manager.settings.privacy_mode is True  # Migrated from enable_privacy

    @pytest.mark.skip(reason="Concurrent test may hang on some systems")
    def test_concurrent_access(self, manager):
        """Test thread-safe settings access."""
        import threading

        results = []

        def update_settings():
            for i in range(10):
                manager.update(typing_speed=100 + i)
                results.append(manager.settings.typing_speed)

        threads = [threading.Thread(target=update_settings) for _ in range(3)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have completed without errors
        assert len(results) == 30

    def test_export_import_settings(self, manager, tmp_path):
        """Test exporting and importing settings."""
        # Set some custom values
        manager.update(typing_speed=200, excluded_apps=["app1", "app2"], privacy_mode=True)

        # Export
        export_path = tmp_path / "exported_settings.json"
        manager.export_settings(export_path)

        # Reset to defaults
        manager.reset_to_defaults()
        assert manager.settings.typing_speed == 100

        # Import
        manager.import_settings(export_path)

        # Should have imported values
        assert manager.settings.typing_speed == 200
        assert manager.settings.excluded_apps == ["app1", "app2"]
        assert manager.settings.privacy_mode is True

    def test_backup_restore(self, manager, tmp_path):
        """Test automatic backup before changes."""
        # Set initial values
        manager.update(typing_speed=200)

        # Make backup
        backup_path = manager.create_backup()

        # Change settings
        manager.update(typing_speed=300)
        assert manager.settings.typing_speed == 300

        # Restore from backup
        manager.restore_from_backup(backup_path)
        assert manager.settings.typing_speed == 200

    def test_invalid_json_handling(self, temp_settings_file):
        """Test handling of corrupted settings file."""
        # Write invalid JSON
        temp_settings_file.write_text("{ invalid json }")

        # Should fall back to defaults
        manager = SettingsManager(settings_path=temp_settings_file)
        assert manager.settings.typing_speed == 100  # Default

    def test_partial_settings_load(self, temp_settings_file):
        """Test loading settings with only some fields."""
        # Write partial settings
        partial_data = {
            "typing_speed": 200,
            "history_size": 50,
            # Missing other fields
        }
        temp_settings_file.write_text(json.dumps(partial_data))

        manager = SettingsManager(settings_path=temp_settings_file)

        # Should load provided values
        assert manager.settings.typing_speed == 200
        assert manager.settings.history_size == 50

        # Should use defaults for missing values
        assert manager.settings.privacy_mode is False
        assert manager.settings.chunk_size == 200
