"""Comprehensive tests for security module to improve coverage."""

from unittest.mock import Mock, patch

import pytest

from pasta.utils.security import (
    PrivacyManager,
    RateLimiter,
    SecurityManager,
    SensitiveDataDetector,
)


class TestSensitiveDataDetectorExtended:
    """Extended tests for SensitiveDataDetector edge cases."""

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

    def test_redact_with_custom_redaction(self):
        """Test redaction with custom redaction string."""
        detector = SensitiveDataDetector()

        text = "Email: test@example.com, Password: secret123"
        redacted = detector.redact_sensitive_data(text, redaction="[HIDDEN]")

        assert "[HIDDEN]" in redacted
        assert "test@example.com" not in redacted
        assert "secret123" not in redacted


class TestRateLimiterExtended:
    """Extended tests for RateLimiter edge cases."""

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

        # Small paste should still be allowed
        assert limiter.is_allowed("paste", size=100) is True

    def test_rate_limit_with_different_actions(self):
        """Test rate limiting across different action types."""
        limiter = RateLimiter()

        # Each action has its own limit
        actions_performed = {"paste": 0, "clipboard": 0, "large_paste": 0}

        # Perform actions up to their limits
        while limiter.is_allowed("paste"):
            actions_performed["paste"] += 1
            if actions_performed["paste"] > 50:  # Safety break
                break

        while limiter.is_allowed("clipboard"):
            actions_performed["clipboard"] += 1
            if actions_performed["clipboard"] > 150:  # Safety break
                break

        # Verify we hit the limits
        assert actions_performed["paste"] == 30  # 30 per 60 seconds
        assert actions_performed["clipboard"] == 100  # 100 per 60 seconds

        # One action being limited shouldn't affect others initially
        assert limiter.is_allowed("paste") is False
        assert limiter.is_allowed("clipboard") is False


class TestPrivacyManagerExtended:
    """Extended tests for PrivacyManager functionality."""

    def test_get_active_window_linux_xdotool_failure(self):
        """Test Linux active window detection when xdotool fails."""
        privacy = PrivacyManager()

        with patch("platform.system", return_value="Linux"), patch("subprocess.run") as mock_run:
            # First call (xdotool) fails
            mock_run.return_value = Mock(returncode=1, stdout="")

            window = privacy._get_active_window()
            assert window == ""

    def test_get_active_window_subprocess_error(self):
        """Test active window detection with subprocess errors."""
        privacy = PrivacyManager()

        with patch("platform.system", return_value="Darwin"), patch("subprocess.run", side_effect=Exception("Command failed")):
            window = privacy._get_active_window()
            assert window == ""

    def test_temporary_privacy_mode_exception_handling(self):
        """Test temporary privacy mode handles exceptions properly."""
        privacy = PrivacyManager()

        # Use temporary privacy mode with exception
        try:
            with privacy.temporary_privacy_mode():
                assert privacy.is_enabled() is True
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Privacy mode should be disabled after exception
        assert privacy.is_enabled() is False

    def test_should_capture_with_excluded_window_patterns(self):
        """Test window pattern exclusion."""
        privacy = PrivacyManager()
        privacy.add_excluded_window_pattern(r".*Password Manager.*")

        # Test pattern matching
        assert privacy.should_capture("normal content", "My Password Manager - Chrome") is False
        assert privacy.should_capture("normal content", "Regular Chrome Window") is True

    def test_should_capture_privacy_mode_enabled(self):
        """Test that nothing is captured when privacy mode is enabled."""
        privacy = PrivacyManager()
        privacy.enable()

        # Should not capture anything in privacy mode
        assert privacy.should_capture("any content", "any window") is False

        privacy.disable()


class TestSecureClipboardExtended:
    """Extended tests for SecureClipboard edge cases."""

    def test_secure_wipe_exception_handling(self):
        """Test secure_wipe handles exceptions gracefully."""
        secure_clipboard = SecurityManager()

        # Create a mock string that raises on encode
        mock_data = Mock()
        mock_data.encode.side_effect = Exception("Encoding error")

        # Should not raise exception
        secure_clipboard.secure_wipe(mock_data)

    def test_cleanup_on_app_exit(self):
        """Test cleanup behavior on application exit."""
        secure_clipboard = SecurityManager()

        # Store some sensitive data
        secure_clipboard.store_secure("password123")
        secure_clipboard.store_secure("api_key_456")

        # Cleanup should wipe all stored data
        secure_clipboard.cleanup()

        # Verify data is wiped (checking internal state)
        assert len(secure_clipboard._secure_storage) == 0

    def test_get_memory_usage(self):
        """Test memory usage calculation."""
        secure_clipboard = SecurityManager()

        # Initially should be minimal
        initial_usage = secure_clipboard.get_memory_usage()
        assert initial_usage >= 0

        # Add some data
        for i in range(100):
            secure_clipboard.store_secure(f"data_{i}" * 100)

        # Usage should increase
        after_usage = secure_clipboard.get_memory_usage()
        assert after_usage > initial_usage

    def test_store_and_wipe_cycle(self):
        """Test multiple store and wipe cycles."""
        secure_clipboard = SecurityManager()

        for i in range(10):
            # Store sensitive data
            data = f"sensitive_data_{i}"
            secure_clipboard.store_secure(data)

            # Verify it's stored
            assert data in str(secure_clipboard._secure_storage)

            # Wipe it
            secure_clipboard.secure_wipe(data)

        # Final cleanup
        secure_clipboard.cleanup()


class TestIntegrationScenarios:
    """Test integration between security components."""

    def test_full_security_flow(self):
        """Test complete security flow with all components."""
        # Initialize components
        detector = SensitiveDataDetector()
        limiter = RateLimiter()
        privacy = PrivacyManager()
        secure_clipboard = SecurityManager()

        # Simulate clipboard content
        clipboard_content = "My password is Secret123! and my email is test@example.com"

        # Check if content is sensitive
        assert detector.is_sensitive(clipboard_content) is True

        # Check rate limiting
        assert limiter.is_allowed("clipboard") is True

        # Check privacy mode
        assert privacy.should_capture(clipboard_content, "Chrome") is True

        # Store securely if sensitive
        if detector.is_sensitive(clipboard_content):
            secure_clipboard.store_secure(clipboard_content)
            # Get redacted version for display
            redacted = detector.redact_sensitive_data(clipboard_content)
            assert "****" in redacted

        # Cleanup
        secure_clipboard.cleanup()

    @patch("time.time")
    def test_rate_limiter_time_window_expiry(self, mock_time):
        """Test rate limiter behavior when time window expires."""
        limiter = RateLimiter()

        # Set initial time
        mock_time.return_value = 1000.0

        # Fill up the limit
        for _ in range(30):
            assert limiter.is_allowed("paste") is True

        # Should be rate limited now
        assert limiter.is_allowed("paste") is False

        # Move time forward past the window (60 seconds)
        mock_time.return_value = 1061.0

        # Should be allowed again
        assert limiter.is_allowed("paste") is True

        # Can fill up the limit again
        for _ in range(29):  # 29 more (30 total including the one above)
            assert limiter.is_allowed("paste") is True

        # Should be rate limited again
        assert limiter.is_allowed("paste") is False
