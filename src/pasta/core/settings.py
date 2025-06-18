"""Settings management for Pasta."""

import json
import os
import platform
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class Settings:
    """Application settings data class.

    This class holds all configurable settings for Pasta.

    Attributes:
        start_on_login: Whether to start Pasta on system login
        monitoring_enabled: Whether clipboard monitoring is enabled
        paste_mode: Default paste mode ('auto', 'clipboard', 'typing')
        typing_speed: Characters per second for typing mode
        chunk_size: Size of text chunks for typing
        adaptive_delay: Whether to use adaptive delays based on system load
        history_size: Maximum number of clipboard entries to keep
        history_retention_days: Days to keep history entries
        encrypt_sensitive: Whether to encrypt sensitive clipboard data
        privacy_mode: Whether privacy mode is enabled
        excluded_apps: List of app names to exclude from monitoring
        excluded_patterns: List of regex patterns to exclude
        emergency_stop_hotkey: Hotkey for emergency stop
        quick_paste_hotkey: Hotkey for quick paste
        toggle_monitoring_hotkey: Hotkey to toggle monitoring
    """

    # General settings
    start_on_login: bool = False
    monitoring_enabled: bool = True
    paste_mode: str = "auto"  # auto, clipboard, typing

    # Performance settings
    typing_speed: int = 100  # characters per second
    chunk_size: int = 200
    adaptive_delay: bool = True

    # History settings
    history_size: int = 100
    history_retention_days: int = 7
    encrypt_sensitive: bool = True

    # Privacy settings
    privacy_mode: bool = False
    excluded_apps: list[str] = field(default_factory=list)
    excluded_patterns: list[str] = field(default_factory=list)

    # Hotkey settings
    emergency_stop_hotkey: str = "esc+esc"
    quick_paste_hotkey: str = ""
    toggle_monitoring_hotkey: str = ""

    def validate(self) -> bool:
        """Validate settings values.

        Returns:
            True if all settings are valid

        Raises:
            ValueError: If any setting is invalid
        """
        # Validate typing speed
        if not 1 <= self.typing_speed <= 1000:
            raise ValueError("Typing speed must be between 1 and 1000 characters per second")

        # Validate history size
        if not 1 <= self.history_size <= 10000:
            raise ValueError("History size must be between 1 and 10000 entries")

        # Validate chunk size
        if not 10 <= self.chunk_size <= 1000:
            raise ValueError("Chunk size must be between 10 and 1000 characters")

        # Validate retention days
        if not 0 <= self.history_retention_days <= 365:
            raise ValueError("Retention days must be between 0 and 365")

        # Validate paste mode
        if self.paste_mode not in ("auto", "clipboard", "typing"):
            raise ValueError(f"Invalid paste mode: {self.paste_mode}")

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary.

        Returns:
            Dictionary representation of settings
        """
        return {
            "start_on_login": self.start_on_login,
            "monitoring_enabled": self.monitoring_enabled,
            "paste_mode": self.paste_mode,
            "typing_speed": self.typing_speed,
            "chunk_size": self.chunk_size,
            "adaptive_delay": self.adaptive_delay,
            "history_size": self.history_size,
            "history_retention_days": self.history_retention_days,
            "encrypt_sensitive": self.encrypt_sensitive,
            "privacy_mode": self.privacy_mode,
            "excluded_apps": self.excluded_apps.copy(),
            "excluded_patterns": self.excluded_patterns.copy(),
            "emergency_stop_hotkey": self.emergency_stop_hotkey,
            "quick_paste_hotkey": self.quick_paste_hotkey,
            "toggle_monitoring_hotkey": self.toggle_monitoring_hotkey,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """Create Settings from dictionary.

        Args:
            data: Dictionary with settings values

        Returns:
            Settings instance
        """
        # Only use known fields
        known_fields = {
            "start_on_login",
            "monitoring_enabled",
            "paste_mode",
            "typing_speed",
            "chunk_size",
            "adaptive_delay",
            "history_size",
            "history_retention_days",
            "encrypt_sensitive",
            "privacy_mode",
            "excluded_apps",
            "excluded_patterns",
            "emergency_stop_hotkey",
            "quick_paste_hotkey",
            "toggle_monitoring_hotkey",
        }

        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

    def copy(self) -> "Settings":
        """Create a deep copy of settings.

        Returns:
            New Settings instance with same values
        """
        return Settings.from_dict(self.to_dict())


class SettingsManager:
    """Manages application settings with persistence.

    This class handles loading, saving, and updating settings,
    as well as notifying observers of changes.

    Attributes:
        settings_path: Path to settings JSON file
        settings: Current Settings instance
        observers: List of observer callbacks
    """

    def __init__(self, settings_path: Optional[Path] = None) -> None:
        """Initialize SettingsManager.

        Args:
            settings_path: Path to settings file (defaults to user config dir)
        """
        if settings_path is None:
            # Use platform-appropriate config directory
            system = platform.system()

            if system == "Darwin":  # macOS
                config_dir = Path.home() / "Library" / "Preferences" / "Pasta"
            elif system == "Windows":
                appdata = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
                config_dir = Path(appdata) / "Pasta"
            else:  # Linux/Unix
                config_dir = Path.home() / ".config" / "pasta"

            config_dir.mkdir(parents=True, exist_ok=True)
            self.settings_path = config_dir / "settings.json"
        else:
            self.settings_path = Path(settings_path)
            if not self.settings_path.parent.exists():
                self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        self.settings = Settings()
        self.observers: list[Callable[[Settings], None]] = []
        self._lock = threading.Lock()

        # Load existing settings
        # Don't auto-load in constructor to avoid issues with tests
        # self.load()

    def load(self) -> None:
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                # Read file outside of lock
                data = json.loads(self.settings_path.read_text())

                # Handle migration from old formats
                data = self._migrate_settings(data)

                # Create and validate settings
                new_settings = Settings.from_dict(data)
                new_settings.validate()

                # Update settings under lock
                with self._lock:
                    self.settings = new_settings
            except (json.JSONDecodeError, ValueError) as e:
                # Fall back to defaults on error
                print(f"Error loading settings: {e}")
                with self._lock:
                    self.settings = Settings()
                self.save()  # Save defaults
        else:
            # Create default settings file
            self.save()

    def save(self) -> None:
        """Save settings to file."""
        # Get data under lock
        with self._lock:
            data = self.settings.to_dict()

        # Add metadata
        data["version"] = 2  # Settings format version
        data["last_updated"] = datetime.now().isoformat()

        # Write to temp file first for atomic operation
        temp_path = self.settings_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, indent=2))

        # Move temp file to final location
        temp_path.replace(self.settings_path)

    def update(self, **kwargs: Any) -> None:
        """Update specific settings.

        Args:
            **kwargs: Settings to update

        Raises:
            ValueError: If validation fails
        """
        with self._lock:
            # Create a copy to validate changes
            new_settings = self.settings.copy()

            # Update fields
            for key, value in kwargs.items():
                if hasattr(new_settings, key):
                    setattr(new_settings, key, value)

            # Validate before applying
            new_settings.validate()

            # Apply changes
            self.settings = new_settings
            self.save()

            # Notify observers
            self._notify_observers()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        with self._lock:
            self.settings = Settings()
            self.save()
            self._notify_observers()

    def add_observer(self, callback: Callable[[Settings], None]) -> None:
        """Add observer for settings changes.

        Args:
            callback: Function to call when settings change
        """
        self.observers.append(callback)

    def remove_observer(self, callback: Callable[[Settings], None]) -> None:
        """Remove observer.

        Args:
            callback: Observer to remove
        """
        if callback in self.observers:
            self.observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of settings change."""
        for observer in self.observers:
            try:
                observer(self.settings)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def export_settings(self, path: Path) -> None:
        """Export settings to file.

        Args:
            path: Path to export file
        """
        with self._lock:
            data = self.settings.to_dict()
            data["exported_at"] = datetime.now().isoformat()
            path.write_text(json.dumps(data, indent=2))

    def import_settings(self, path: Path) -> None:
        """Import settings from file.

        Args:
            path: Path to import file

        Raises:
            ValueError: If import file is invalid
        """
        try:
            data = json.loads(path.read_text())
            new_settings = Settings.from_dict(data)
            new_settings.validate()

            with self._lock:
                self.settings = new_settings
                self.save()
                self._notify_observers()
        except Exception as e:
            raise ValueError(f"Failed to import settings: {e}") from e

    def create_backup(self) -> Path:
        """Create backup of current settings.

        Returns:
            Path to backup file
        """
        backup_dir = self.settings_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"settings_backup_{timestamp}.json"

        with self._lock:
            shutil.copy2(self.settings_path, backup_path)

        return backup_path

    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore settings from backup.

        Args:
            backup_path: Path to backup file
        """
        # Import handles validation
        self.import_settings(backup_path)

    def _migrate_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate settings from old format.

        Args:
            data: Settings data to migrate

        Returns:
            Migrated settings data
        """
        version = data.get("version", 1)

        if version == 1:
            # Migrate from version 1 to 2
            if "history_limit" in data:
                data["history_size"] = data.pop("history_limit")
            if "enable_privacy" in data:
                data["privacy_mode"] = data.pop("enable_privacy")

        return data
