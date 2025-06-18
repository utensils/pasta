"""Additional tests for Settings module to improve coverage."""

import json
from unittest.mock import Mock

import pytest

from pasta.core.settings import Settings, SettingsManager


class TestSettingsCoverage:
    """Additional test cases for Settings module coverage."""

    @pytest.fixture
    def temp_settings_file(self, tmp_path):
        """Create a temporary settings file."""
        return tmp_path / "settings.json"

    @pytest.fixture
    def manager(self, temp_settings_file):
        """Create a SettingsManager with temp file."""
        return SettingsManager(temp_settings_file)

    def test_load_with_migration(self, manager, temp_settings_file):
        """Test loading settings that need migration."""
        # Create old format settings
        old_settings = {
            "version": 1,
            "history_limit": 50,  # Old name
            "enable_privacy": True,  # Old name
            "typing_speed": 100,
        }
        temp_settings_file.write_text(json.dumps(old_settings))

        # Load settings
        manager.load()

        # Should have migrated old fields
        assert manager.settings.history_size == 50
        assert manager.settings.privacy_mode is True
        assert manager.settings.typing_speed == 100

    def test_load_with_json_error(self, manager, temp_settings_file):
        """Test loading with invalid JSON."""
        # Write invalid JSON
        temp_settings_file.write_text("{ invalid json }")

        # Load should fall back to defaults
        manager.load()

        # Should have default settings
        assert manager.settings.typing_speed == 100  # Default value

    def test_load_with_validation_error(self, manager, temp_settings_file):
        """Test loading with invalid settings values."""
        # Create settings with invalid values
        invalid_settings = {
            "typing_speed": 2000,  # Too high
            "history_size": 100,
        }
        temp_settings_file.write_text(json.dumps(invalid_settings))

        # Load should fall back to defaults due to validation error
        manager.load()

        # Should have default settings
        assert manager.settings.typing_speed == 100  # Default value

    def test_load_creates_default_file(self, manager, temp_settings_file):
        """Test that load creates default settings file if missing."""
        # Ensure file doesn't exist
        if temp_settings_file.exists():
            temp_settings_file.unlink()

        # Load settings
        manager.load()

        # Should create file with defaults
        assert temp_settings_file.exists()
        data = json.loads(temp_settings_file.read_text())
        assert "version" in data
        assert "last_updated" in data

    def test_update_with_validation_error(self, manager):
        """Test update that fails validation."""
        with pytest.raises(ValueError, match="Typing speed must be between"):
            manager.update(typing_speed=2000)  # Too high

    def test_observer_error_handling(self, manager):
        """Test that observer errors don't stop notifications."""
        good_observer = Mock()
        bad_observer = Mock(side_effect=Exception("Observer error"))
        another_good_observer = Mock()

        manager.add_observer(good_observer)
        manager.add_observer(bad_observer)
        manager.add_observer(another_good_observer)

        # Update settings
        manager.update(typing_speed=150)

        # All observers should be called despite error
        good_observer.assert_called_once()
        bad_observer.assert_called_once()
        another_good_observer.assert_called_once()

    def test_migrate_settings_no_version(self, manager):
        """Test migration when no version is specified."""
        data = {
            "history_limit": 75,
            "typing_speed": 100,
        }

        migrated = manager._migrate_settings(data)

        # Should migrate from v1
        assert "history_size" in migrated
        assert migrated["history_size"] == 75
        assert "history_limit" not in migrated

    def test_settings_validation_edge_cases(self):
        """Test Settings validation edge cases."""
        settings = Settings()

        # Test boundary values
        settings.typing_speed = 1
        assert settings.validate()

        settings.typing_speed = 1000
        assert settings.validate()

        settings.history_size = 1
        assert settings.validate()

        settings.history_size = 10000
        assert settings.validate()

        settings.chunk_size = 10
        assert settings.validate()

        settings.chunk_size = 1000
        assert settings.validate()

        settings.history_retention_days = 0
        assert settings.validate()

        settings.history_retention_days = 365
        assert settings.validate()
