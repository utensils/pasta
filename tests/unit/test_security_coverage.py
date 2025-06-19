"""Tests for security module to improve coverage."""

import json

import pytest

from pasta.utils.security import (
    PrivacyManager,
    RateLimiter,
    SecurityManager,
    SensitiveDataDetector,
)


class TestSensitiveDataDetectorCoverage:
    """Tests for SensitiveDataDetector coverage gaps."""

    def test_add_custom_pattern_invalid_regex(self):
        """Test adding invalid regex pattern."""
        detector = SensitiveDataDetector()

        with pytest.raises(ValueError, match="Invalid regex pattern"):
            detector.add_custom_pattern("invalid_pattern", "[invalid(regex")

    def test_add_custom_pattern_valid(self):
        """Test adding valid custom pattern."""
        detector = SensitiveDataDetector()

        # Add custom pattern
        detector.add_custom_pattern("custom_id", r"ID-\d{6}")

        # Test detection with custom pattern
        assert detector.is_sensitive("My ID is ID-123456") is True
        assert detector.is_sensitive("No ID here") is False

    def test_get_detected_types_with_custom_patterns(self):
        """Test detected types including custom patterns."""
        detector = SensitiveDataDetector()
        detector.add_custom_pattern("employee_id", r"EMP-\d{4}")

        text = "Email: test@example.com, Employee: EMP-1234"
        assert detector.is_sensitive(text) is True

        detected = detector.get_detected_types(text)
        # Email is not detected by default
        assert "employee_id" in detected


class TestRateLimiterCoverage:
    """Tests for RateLimiter coverage gaps."""

    def test_unknown_action_always_allowed(self):
        """Test that unknown actions are always allowed."""
        limiter = RateLimiter()

        # Unknown action should always be allowed
        for _ in range(100):
            assert limiter.is_allowed("unknown_action") is True

    def test_large_paste_auto_detection(self):
        """Test automatic large paste detection."""
        limiter = RateLimiter()

        # Regular paste with large size should be treated as large_paste
        # Fill up the large_paste limit
        for _ in range(5):
            assert limiter.is_allowed("paste", size=15000) is True

        # Next large paste should be rate limited
        assert limiter.is_allowed("paste", size=15000) is False

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading rate limiter state."""
        limiter = RateLimiter()

        # Perform some actions
        for _ in range(10):
            limiter.is_allowed("paste")

        # Save state
        state_file = tmp_path / "rate_limiter_state.json"
        limiter.save_state(str(state_file))

        assert state_file.exists()

        # Create new limiter and load state
        new_limiter = RateLimiter()
        new_limiter.load_state(str(state_file))

        # Should have same history
        assert len(new_limiter.history["paste"]) == 10

    def test_load_state_with_invalid_file(self):
        """Test loading state from invalid file."""
        limiter = RateLimiter()

        # Should not raise exception
        limiter.load_state("/nonexistent/file.json")

        # Should still work normally
        assert limiter.is_allowed("paste") is True

    def test_reset_action(self):
        """Test resetting specific action limits."""
        limiter = RateLimiter()

        # Fill up paste limit
        for _ in range(30):
            limiter.is_allowed("paste")

        assert limiter.is_allowed("paste") is False

        # Reset paste action
        limiter.reset_action("paste")

        # Should be allowed again
        assert limiter.is_allowed("paste") is True

    def test_reset_nonexistent_action(self):
        """Test resetting action that doesn't exist."""
        limiter = RateLimiter()

        # Should not raise exception
        limiter.reset_action("nonexistent_action")


class TestPrivacyManagerCoverage:
    """Tests for PrivacyManager coverage gaps."""

    def test_privacy_mode_blocks_all(self):
        """Test that privacy mode blocks all captures."""
        privacy = PrivacyManager()
        privacy.set_privacy_mode(True)

        assert privacy.should_capture("any window", "any content") is False

    def test_excluded_patterns_invalid_regex(self):
        """Test adding invalid regex pattern."""
        privacy = PrivacyManager()

        with pytest.raises(ValueError, match="Invalid regex pattern"):
            privacy.add_excluded_pattern("[invalid(")

    def test_export_import_settings(self, tmp_path):
        """Test export and import of privacy settings."""
        privacy = PrivacyManager()

        # Configure settings
        privacy.set_privacy_mode(True)
        privacy.add_excluded_app("KeePass")
        privacy.add_excluded_pattern(r"password:\s*\S+")

        # Export
        export_file = tmp_path / "privacy_settings.json"
        privacy.export_settings(export_file)

        # Create new instance and import
        new_privacy = PrivacyManager()
        new_privacy.import_settings(export_file)

        assert new_privacy.privacy_mode is True
        assert "keepass" in new_privacy.excluded_apps
        assert r"password:\s*\S+" in new_privacy.excluded_patterns

    def test_import_invalid_settings(self, tmp_path):
        """Test importing invalid settings file."""
        privacy = PrivacyManager()

        # Create invalid file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not json")

        with pytest.raises(ValueError, match="Failed to import settings"):
            privacy.import_settings(invalid_file)

    def test_import_settings_with_invalid_pattern(self, tmp_path):
        """Test importing settings with invalid regex pattern."""
        privacy = PrivacyManager()

        # Create file with invalid pattern
        settings = {"privacy_mode": False, "excluded_apps": [], "excluded_patterns": ["[invalid(regex"]}

        invalid_file = tmp_path / "bad_patterns.json"
        invalid_file.write_text(json.dumps(settings))

        with pytest.raises(ValueError):
            privacy.import_settings(invalid_file)


class TestSecurityManagerCoverage:
    """Tests for SecurityManager coverage gaps."""

    def test_security_check_flow(self):
        """Test complete security check flow."""
        manager = SecurityManager()

        # Test sensitive content detection
        content = "My password is Secret123!"
        assert manager.is_sensitive(content) is True

        # Test rate limiting
        assert manager.check_rate_limit("paste") is True

        # Test privacy mode
        manager.enable_privacy_mode()
        assert manager.should_process("test", "TestApp") is False

        manager.disable_privacy_mode()
        assert manager.should_process("test", "TestApp") is True

    def test_should_process_with_excluded_app(self):
        """Test should_process with excluded app."""
        manager = SecurityManager()

        # Should not process content from password managers
        assert manager.should_process("password", "1Password") is False
        assert manager.should_process("password", "KeePass") is False

    def test_audit_logging(self):
        """Test audit logging functionality."""
        manager = SecurityManager()

        # Set up audit callback
        audit_logs = []
        manager.set_audit_callback(lambda action, data: audit_logs.append((action, data)))

        # Perform actions that trigger auditing
        manager.check_rate_limit("paste", size=20000)  # Large paste

        # Check audit log
        assert len(audit_logs) >= 1
        assert audit_logs[0][0] == "large_paste_detected"

    def test_enable_disable_privacy_mode(self):
        """Test enabling and disabling privacy mode."""
        manager = SecurityManager()

        # Initially disabled
        assert manager._privacy_mode is False

        # Enable
        manager.enable_privacy_mode()
        assert manager._privacy_mode is True

        # Disable
        manager.disable_privacy_mode()
        assert manager._privacy_mode is False

    def test_reset_rate_limits(self):
        """Test resetting all rate limits."""
        manager = SecurityManager()

        # Fill up some limits by recording requests
        for _ in range(30):
            manager.limiter.record_request("paste")

        # Should be rate limited
        assert manager.check_rate_limit("paste") is False

        # Reset all limits
        manager.reset_rate_limits()

        # Should be allowed again
        assert manager.check_rate_limit("paste") is True

    def test_get_security_status(self):
        """Test getting security status summary."""
        manager = SecurityManager()

        status = manager.get_security_status()

        assert isinstance(status, dict)
        assert "privacy_mode" in status
        assert "rate_limits" in status
        assert "excluded_apps" in status
