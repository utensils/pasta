"""Security utilities for Pasta."""

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional


class SensitiveDataDetector:
    """Detects sensitive data in clipboard content.

    This class identifies various types of sensitive information
    like credit cards, SSNs, passwords, etc.

    Attributes:
        patterns: Dictionary of regex patterns for sensitive data
    """

    def __init__(self) -> None:
        """Initialize the sensitive data detector."""
        self.patterns: dict[str, str] = {
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{3} \d{2} \d{4}\b",
            "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",
            "password": r"(?i)(password|passwd|pwd)[\s:=]+\S+",
            "api_key": r"(?i)(api[-_]?key|apikey|secret)[\s:=]+\S+",
            "private_key": r"-----BEGIN\s+(RSA|EC|OPENSSH)?\s*PRIVATE KEY-----",
        }

    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive data.

        Args:
            text: Text to check

        Returns:
            True if sensitive data is detected
        """
        return any(re.search(pattern, text) for pattern in self.patterns.values())

    def get_detected_types(self, text: str) -> list[str]:
        """Get types of sensitive data detected in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected sensitive data types
        """
        detected = []
        for data_type, pattern in self.patterns.items():
            if re.search(pattern, text):
                detected.append(data_type)
        return detected

    def add_pattern(self, pattern: str, name: str) -> None:
        """Add a custom pattern for sensitive data detection.

        Args:
            pattern: Regex pattern to add
            name: Name for this pattern type

        Raises:
            ValueError: If pattern is invalid regex
        """
        try:
            re.compile(pattern)
            self.patterns[name] = pattern
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    def redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text.

        Args:
            text: Text to redact

        Returns:
            Text with sensitive data replaced by [REDACTED]
        """
        redacted = text
        for pattern in self.patterns.values():
            redacted = re.sub(pattern, "[REDACTED]", redacted)
        return redacted


class RateLimiter:
    """Rate limiter to prevent abuse and system overload.

    This class implements a sliding window rate limiter
    for different types of operations.

    Attributes:
        limits: Dictionary of action limits (count, window_seconds)
        history: Dictionary tracking action timestamps
    """

    def __init__(self, limits: Optional[dict[str, tuple[int, int]]] = None) -> None:
        """Initialize the rate limiter.

        Args:
            limits: Custom rate limits or None for defaults
        """
        self.limits = limits or {
            "paste": (30, 60),  # 30 pastes per 60 seconds
            "clipboard": (100, 60),  # 100 clipboard reads per 60 seconds
            "large_paste": (5, 300),  # 5 large pastes per 5 minutes
        }
        self.history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, action: str, size: Optional[int] = None) -> bool:
        """Check if action is allowed under rate limits.

        Args:
            action: Type of action to check
            size: Size of data (for auto-detecting large operations)

        Returns:
            True if action is allowed
        """
        # Auto-detect large paste
        if action == "paste" and size and size > 10000:
            action = "large_paste"

        # Unknown actions are always allowed
        if action not in self.limits:
            return True

        max_count, window_seconds = self.limits[action]
        now = time.time()
        cutoff = now - window_seconds

        # Clean old entries
        self.history[action] = [t for t in self.history[action] if t > cutoff]

        # Check limit
        if len(self.history[action]) >= max_count:
            return False

        # Record action
        self.history[action].append(now)
        return True

    def get_remaining_quota(self, action: str) -> Optional[int]:
        """Get remaining quota for an action.

        Args:
            action: Action to check

        Returns:
            Remaining allowed actions or None if unlimited
        """
        if action not in self.limits:
            return None

        max_count, window_seconds = self.limits[action]
        now = time.time()
        cutoff = now - window_seconds

        # Count recent actions
        recent_count = sum(1 for t in self.history[action] if t > cutoff)
        return max_count - recent_count

    def reset_action(self, action: str) -> None:
        """Reset rate limit for specific action.

        Args:
            action: Action to reset
        """
        if action in self.history:
            self.history[action].clear()


class PrivacyManager:
    """Manages privacy settings and exclusions.

    This class handles privacy mode, excluded applications,
    and content patterns that should not be captured.

    Attributes:
        privacy_mode: Whether privacy mode is enabled
        excluded_apps: Set of excluded application names
        excluded_patterns: List of regex patterns to exclude
    """

    def __init__(self, default_excluded_apps: Optional[list[str]] = None) -> None:
        """Initialize the privacy manager.

        Args:
            default_excluded_apps: List of apps to exclude by default
        """
        self.privacy_mode = False
        self.excluded_apps: set[str] = set()
        self.excluded_patterns: list[str] = []

        # Add default exclusions
        if default_excluded_apps:
            for app in default_excluded_apps:
                self.add_excluded_app(app)

    def should_capture(self, active_window: str, content: str) -> bool:
        """Determine if content should be captured.

        Args:
            active_window: Name of the active window/application
            content: Clipboard content

        Returns:
            True if content should be captured
        """
        # Privacy mode blocks everything
        if self.privacy_mode:
            return False

        # Check excluded applications
        window_lower = active_window.lower()
        if any(app in window_lower for app in self.excluded_apps):
            return False

        # Check excluded patterns
        return all(not re.search(pattern, content) for pattern in self.excluded_patterns)

    def set_privacy_mode(self, enabled: bool) -> None:
        """Enable or disable privacy mode.

        Args:
            enabled: Whether to enable privacy mode
        """
        self.privacy_mode = enabled

    def add_excluded_app(self, app_name: str) -> None:
        """Add an application to the exclusion list.

        Args:
            app_name: Name of the application to exclude
        """
        self.excluded_apps.add(app_name.lower())

    def remove_excluded_app(self, app_name: str) -> None:
        """Remove an application from the exclusion list.

        Args:
            app_name: Name of the application to remove
        """
        self.excluded_apps.discard(app_name.lower())

    def add_excluded_pattern(self, pattern: str) -> None:
        """Add a regex pattern to exclude.

        Args:
            pattern: Regex pattern to add

        Raises:
            ValueError: If pattern is invalid regex
        """
        try:
            re.compile(pattern)
            self.excluded_patterns.append(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

    def get_excluded_apps(self) -> list[str]:
        """Get list of excluded applications.

        Returns:
            List of excluded app names
        """
        return sorted(self.excluded_apps)

    def clear_exclusions(self) -> None:
        """Clear all exclusions (apps and patterns)."""
        self.excluded_apps.clear()
        self.excluded_patterns.clear()

    def export_settings(self, path: Path) -> None:
        """Export privacy settings to file.

        Args:
            path: Path to export file
        """
        settings = {
            "privacy_mode": self.privacy_mode,
            "excluded_apps": list(self.excluded_apps),
            "excluded_patterns": self.excluded_patterns,
        }
        path.write_text(json.dumps(settings, indent=2))

    def import_settings(self, path: Path) -> None:
        """Import privacy settings from file.

        Args:
            path: Path to import file

        Raises:
            ValueError: If import file is invalid
        """
        try:
            data = json.loads(path.read_text())
            self.privacy_mode = data.get("privacy_mode", False)
            self.excluded_apps = set(data.get("excluded_apps", []))
            self.excluded_patterns = data.get("excluded_patterns", [])

            # Validate patterns
            for pattern in self.excluded_patterns:
                re.compile(pattern)
        except Exception as e:
            raise ValueError(f"Failed to import settings: {e}") from e


# Keep the original SecurityManager for backward compatibility
class SecurityManager:
    """Legacy security manager for backward compatibility.

    This class wraps the new modular security components.

    Attributes:
        detector: SensitiveDataDetector instance
        limiter: RateLimiter instance
        privacy: PrivacyManager instance
    """

    def __init__(self, encryption_key: Optional[bytes] = None) -> None:
        """Initialize the SecurityManager.

        Args:
            encryption_key: Optional encryption key (for future use)
        """
        self.encryption_key = encryption_key
        self.detector = SensitiveDataDetector()
        self.limiter = RateLimiter()
        self.privacy = PrivacyManager()

    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive data.

        Args:
            text: Text to check

        Returns:
            True if text contains sensitive data
        """
        return self.detector.is_sensitive(text)
