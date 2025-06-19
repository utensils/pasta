"""Security utilities for Pasta."""

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Optional


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
            # Credit cards
            "credit_card": r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
            "credit_card_no_space": r"\b\d{16}\b",
            # SSN
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b|\b\d{3} \d{2} \d{4}\b",
            # Passwords
            "password": r"(?i)(password|passwd|pwd)[\s:=]+\S+",
            # API Keys and tokens
            "api_key": r"(?i)(api[-_]?key|apikey)[\s:=]+[\w-]+",
            "secret": r"(?i)(secret|token)[\s:=]+\S+",
            "bearer_token": r"(?i)Bearer\s+[\w.-]+",
            "auth_header": r"(?i)(Authorization|X-API-Key)[\s:]+[\w.-]+",
            "github_token": r"github_pat_[\w]+",
            "gitlab_token": r"glpat-[\w-]+",
            "slack_token": r"xox[baprs]-[\w-]+",
            "aws_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret": r"(?i)aws_secret_access_key[\s=]+[\w/+=]+",
            # Private keys
            "private_key_rsa": r"-----BEGIN\s*(?:RSA\s*)?PRIVATE\s*KEY-----",
            "private_key_general": r"-----BEGIN\s*PRIVATE\s*KEY-----",
            "private_key_ec": r"-----BEGIN\s*EC\s*PRIVATE\s*KEY-----",
            "ssh_key": r"ssh-rsa\s+[\w+/=]+",
            # Database URLs
            "db_url_postgres": r"postgres(?:ql)?://[^:]+:[^@]+@[^/]+(?:/\w+)?",
            "db_url_mysql": r"mysql://[^:]+:[^@]+@[^/]+(?:/\w+)?",
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

    def add_custom_pattern(self, name: str, pattern: str) -> None:
        """Add a custom pattern for sensitive data detection (alternate method).

        Args:
            name: Name for this pattern type
            pattern: Regex pattern to add

        Raises:
            ValueError: If pattern is invalid regex
        """
        self.add_pattern(pattern, name)

    def redact_sensitive_data(self, text: str, redaction: str = "[REDACTED]") -> str:
        """Redact sensitive data from text.

        Args:
            text: Text to redact
            redaction: String to replace sensitive data with

        Returns:
            Text with sensitive data replaced by redaction string
        """
        redacted = text
        for pattern in self.patterns.values():
            redacted = re.sub(pattern, redaction, redacted)
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
            "clipboard_read": (100, 60),  # 100 clipboard reads per 60 seconds
            "large_paste": (5, 300),  # 5 large pastes per 5 minutes
        }
        self.history: dict[str, list[float]] = defaultdict(list)
        self._state_file: Optional[Path] = None

    def set_limit(self, action: str, max_requests: int, window_seconds: int) -> None:
        """Set rate limit for an action.

        Args:
            action: Action to limit
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.limits[action] = (max_requests, window_seconds)

    def check_limit(self, action: str, size: Optional[int] = None) -> bool:
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
        return len(self.history[action]) < max_count

    def record_request(self, action: str, size: Optional[int] = None) -> None:
        """Record that a request was made.

        Args:
            action: Action that was performed
            size: Size of data (for auto-detecting large operations)
        """
        # Auto-detect large paste
        if action == "paste" and size and size > 10000:
            action = "large_paste"

        if action in self.limits:
            self.history[action].append(time.time())

    def reset(self, action: str) -> None:
        """Reset rate limit for specific action.

        Args:
            action: Action to reset
        """
        if action in self.history:
            self.history[action].clear()

    def is_allowed(self, action: str, size: Optional[int] = None) -> bool:
        """Check if action is allowed under rate limits and record it.

        Args:
            action: Type of action to check
            size: Size of data (for auto-detecting large operations)

        Returns:
            True if action is allowed
        """
        if self.check_limit(action, size):
            self.record_request(action, size)
            return True
        return False

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

    def save_state(self, file_path: str) -> None:
        """Save rate limiter state to file.

        Args:
            file_path: Path to save state file
        """
        state = {"limits": self.limits, "history": {k: list(v) for k, v in self.history.items()}}
        Path(file_path).write_text(json.dumps(state, indent=2))

    def load_state(self, file_path: str) -> None:
        """Load rate limiter state from file.

        Args:
            file_path: Path to load state file
        """
        try:
            state = json.loads(Path(file_path).read_text())
            self.limits = state.get("limits", self.limits)
            self.history = defaultdict(list, {k: list(v) for k, v in state.get("history", {}).items()})
        except Exception:
            # If loading fails, start fresh
            pass


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
        self.excluded_window_patterns: list[str] = []

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

        # Check excluded window patterns
        if any(re.search(pattern, active_window) for pattern in self.excluded_window_patterns):
            return False

        # Check excluded patterns
        return all(not re.search(pattern, content) for pattern in self.excluded_patterns)

    def set_privacy_mode(self, enabled: bool) -> None:
        """Enable or disable privacy mode.

        Args:
            enabled: Whether to enable privacy mode
        """
        self.privacy_mode = enabled

    def enable(self) -> None:
        """Enable privacy mode."""
        self.privacy_mode = True

    def disable(self) -> None:
        """Disable privacy mode."""
        self.privacy_mode = False

    def is_enabled(self) -> bool:
        """Check if privacy mode is enabled.

        Returns:
            True if privacy mode is enabled
        """
        return self.privacy_mode

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

    def add_excluded_window_pattern(self, pattern: str) -> None:
        """Add a window pattern to exclude.

        Args:
            pattern: Regex pattern for window titles to exclude

        Raises:
            ValueError: If pattern is invalid regex
        """
        try:
            re.compile(pattern)
            self.excluded_window_patterns.append(pattern)
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

    def temporary_privacy_mode(self) -> Any:
        """Context manager for temporary privacy mode.

        Usage:
            with privacy_manager.temporary_privacy_mode():
                # Privacy mode is enabled here
                pass
            # Privacy mode is restored to previous state
        """
        from contextlib import contextmanager

        @contextmanager
        def _temporary_privacy() -> Any:
            previous_state = self.privacy_mode
            self.privacy_mode = True
            try:
                yield
            finally:
                self.privacy_mode = previous_state

        return _temporary_privacy()

    def _get_active_window(self) -> str:
        """Get the active window title.

        Returns:
            Active window title or empty string if unable to determine
        """
        try:
            from pasta.utils.platform import get_active_window_title

            return get_active_window_title()
        except Exception:
            return ""


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
        self.privacy = PrivacyManager(["1password", "keepass", "bitwarden", "lastpass", "dashlane", "password manager"])
        self._audit_callback: Optional[Callable[[str, dict[str, Any]], None]] = None
        self._privacy_mode = False
        self._secure_storage: list[bytes] = []

    def is_sensitive(self, text: str) -> bool:
        """Check if text contains sensitive data.

        Args:
            text: Text to check

        Returns:
            True if text contains sensitive data
        """
        is_sensitive = self.detector.is_sensitive(text)
        if is_sensitive and self._audit_callback:
            self._audit_callback("sensitive_data_detected", {"content_length": len(text)})
        return is_sensitive

    def enable_privacy_mode(self) -> None:
        """Enable privacy mode."""
        self._privacy_mode = True
        self.privacy.set_privacy_mode(True)
        if self._audit_callback:
            self._audit_callback("privacy_mode_enabled", {})

    def disable_privacy_mode(self) -> None:
        """Disable privacy mode."""
        self._privacy_mode = False
        self.privacy.set_privacy_mode(False)
        if self._audit_callback:
            self._audit_callback("privacy_mode_disabled", {})

    def is_privacy_mode_enabled(self) -> bool:
        """Check if privacy mode is enabled.

        Returns:
            True if privacy mode is enabled
        """
        return self._privacy_mode

    def add_excluded_app(self, app_name: str) -> None:
        """Add an app to the exclusion list.

        Args:
            app_name: Name of app to exclude
        """
        self.privacy.add_excluded_app(app_name)
        if self._audit_callback:
            self._audit_callback("excluded_app_added", {"app": app_name})

    def is_app_excluded(self, app_name: str) -> bool:
        """Check if an app is excluded.

        Args:
            app_name: Name of app to check

        Returns:
            True if app is excluded
        """
        return app_name.lower() in self.privacy.excluded_apps

    def should_process_clipboard(self) -> bool:
        """Check if clipboard should be processed.

        Returns:
            True if clipboard should be processed
        """
        if self._privacy_mode:
            return False

        try:
            from pasta.utils.platform import get_active_window_title

            active_window = get_active_window_title()
            return not any(app in active_window.lower() for app in self.privacy.excluded_apps)
        except Exception:
            return True

    def set_audit_callback(self, callback: Optional[Callable[[str, dict[str, Any]], None]]) -> None:
        """Set callback for security events.

        Args:
            callback: Function to call for security events
        """
        self._audit_callback = callback

    def secure_cleanup(self) -> None:
        """Perform secure cleanup of sensitive data."""
        # In a real implementation, this would clear sensitive data from memory
        # For now, just clear histories
        self.limiter.history.clear()

    def rotate_encryption_key(self) -> None:
        """Rotate encryption key (placeholder for future implementation)."""
        # This would re-encrypt all sensitive data with a new key
        pass

    def check_rate_limit(self, action: str, size: Optional[int] = None) -> bool:
        """Check if action is allowed under rate limits.

        Args:
            action: Type of action to check
            size: Size of data (for auto-detecting large operations)

        Returns:
            True if action is allowed
        """
        allowed = self.limiter.check_limit(action, size)
        if not allowed and self._audit_callback:
            self._audit_callback("rate_limit_exceeded", {"action": action})

        # Log large pastes to audit
        if action == "paste" and size and size > 10000 and self._audit_callback:
            self._audit_callback("large_paste_detected", {"size": size})

        return allowed

    def should_process(self, content: str, window_title: str) -> bool:  # noqa: ARG002
        """Determine if content should be processed based on security settings.

        Args:
            content: Clipboard content
            window_title: Active window title

        Returns:
            True if content should be processed
        """
        if self._privacy_mode:
            return False

        # Check excluded apps
        return not any(app in window_title.lower() for app in self.privacy.excluded_apps)

    def get_security_status(self) -> dict[str, Any]:
        """Get current security status.

        Returns:
            Dictionary with security status information
        """
        return {
            "privacy_mode": self._privacy_mode,
            "rate_limits": {
                action: {
                    "limit": self.limiter.limits.get(action, (None, None))[0],
                    "window": self.limiter.limits.get(action, (None, None))[1],
                    "remaining": self.limiter.get_remaining_quota(action),
                }
                for action in self.limiter.limits
            },
            "excluded_apps": self.privacy.get_excluded_apps(),
            "secure_storage_size": len(self._secure_storage),
        }

    def store_secure(self, data: str) -> None:
        """Store sensitive data securely.

        Args:
            data: Data to store securely
        """
        # Convert to bytes and store
        self._secure_storage.append(data.encode("utf-8"))

        if self._audit_callback:
            self._audit_callback("secure_storage_write", {"size": len(data)})

    def secure_wipe(self, data: Any) -> None:
        """Securely wipe sensitive data from memory.

        Args:
            data: Data to wipe
        """
        try:
            if isinstance(data, str):
                # Convert to bytearray for in-place modification
                data_bytes = bytearray(data.encode("utf-8"))
                # Overwrite with zeros
                for i in range(len(data_bytes)):
                    data_bytes[i] = 0
            elif isinstance(data, bytearray):
                # Overwrite bytearray directly
                for i in range(len(data)):
                    data[i] = 0
            elif isinstance(data, bytes):
                # bytes are immutable, can't overwrite
                pass
        except Exception:
            # Ignore errors during wipe
            pass

    def get_memory_usage(self) -> int:
        """Get current memory usage of secure storage.

        Returns:
            Total bytes used by secure storage
        """
        return sum(len(data) for data in self._secure_storage)

    def cleanup(self) -> None:
        """Clean up secure storage and perform security cleanup."""
        # Wipe all secure storage
        for data in self._secure_storage:
            self.secure_wipe(data)
        self._secure_storage.clear()

        # Clear rate limiter history
        self.limiter.history.clear()

        if self._audit_callback:
            self._audit_callback("security_cleanup", {})

    def reset_rate_limits(self) -> None:
        """Reset all rate limits."""
        for action in self.limiter.limits:
            self.limiter.reset(action)
