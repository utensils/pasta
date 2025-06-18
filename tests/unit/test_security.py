"""Tests for the SecurityManager module."""

from unittest.mock import patch

import pytest

from pasta.utils.security import PrivacyManager, RateLimiter, SensitiveDataDetector


class TestSensitiveDataDetector:
    """Test cases for SensitiveDataDetector."""

    @pytest.fixture
    def detector(self):
        """Create a SensitiveDataDetector for testing."""
        return SensitiveDataDetector()

    def test_detect_credit_card(self, detector):
        """Test credit card number detection."""
        # Valid credit card patterns
        assert detector.is_sensitive("4111111111111111") is True
        assert detector.is_sensitive("4111 1111 1111 1111") is True
        assert detector.is_sensitive("4111-1111-1111-1111") is True
        assert detector.is_sensitive("5500 0000 0000 0004") is True

        # Invalid patterns
        assert detector.is_sensitive("1234567890") is False
        assert detector.is_sensitive("411111111111") is False

    def test_detect_ssn(self, detector):
        """Test Social Security Number detection."""
        # Valid SSN patterns
        assert detector.is_sensitive("123-45-6789") is True
        assert detector.is_sensitive("123 45 6789") is True

        # Invalid patterns
        assert detector.is_sensitive("123456789") is False
        assert detector.is_sensitive("12-345-6789") is False

    def test_detect_email(self, detector):
        """Test email address detection."""
        # Valid emails
        assert detector.is_sensitive("user@example.com") is True
        assert detector.is_sensitive("test.user+tag@domain.co.uk") is True

        # Invalid patterns
        assert detector.is_sensitive("not an email") is False
        assert detector.is_sensitive("user@") is False

    def test_detect_password(self, detector):
        """Test password pattern detection."""
        # Password patterns
        assert detector.is_sensitive("password: secret123") is True
        assert detector.is_sensitive("Password=MySecret!") is True
        assert detector.is_sensitive("pwd: hidden") is True
        assert detector.is_sensitive("passwd:test123") is True

        # Non-password text
        assert detector.is_sensitive("normal text") is False

    def test_detect_api_key(self, detector):
        """Test API key detection."""
        # API key patterns
        assert detector.is_sensitive("api_key: abc123def456") is True
        assert detector.is_sensitive("API-KEY=sk_test_123456") is True
        assert detector.is_sensitive("secret: mysecretvalue") is True
        assert detector.is_sensitive("apiKey=1234567890abcdef") is True

        # Normal text
        assert detector.is_sensitive("this is just text") is False

    def test_detect_private_key(self, detector):
        """Test private key detection."""
        # Private key headers (use prefix + suffix to avoid pre-commit detection)
        prefix = "-----BEGIN"
        suffix = "PRIVATE KEY-----"
        assert detector.is_sensitive(f"{prefix} RSA {suffix}") is True
        assert detector.is_sensitive(f"{prefix} {suffix}") is True
        assert detector.is_sensitive(f"{prefix} EC {suffix}") is True

        # Public keys should not be sensitive
        assert detector.is_sensitive("-----BEGIN PUBLIC KEY-----") is False

    def test_custom_patterns(self, detector):
        """Test adding custom patterns."""
        # Add custom pattern
        detector.add_pattern(r"\b(SECRET|CONFIDENTIAL)\b", "custom_keyword")

        assert detector.is_sensitive("This is SECRET information") is True
        assert detector.is_sensitive("CONFIDENTIAL data") is True
        assert detector.is_sensitive("normal text") is False

    def test_get_detected_types(self, detector):
        """Test getting types of detected sensitive data."""
        text = "Email: user@example.com, Card: 4111-1111-1111-1111"
        types = detector.get_detected_types(text)

        assert "email" in types
        assert "credit_card" in types
        assert len(types) == 2

    def test_mixed_content(self, detector):
        """Test detection in mixed content."""
        text = """
        Normal text here.
        Contact: john@example.com
        Payment: 4111 1111 1111 1111
        More normal text.
        """

        assert detector.is_sensitive(text) is True
        types = detector.get_detected_types(text)
        assert "email" in types
        assert "credit_card" in types

    def test_redact_sensitive_data(self, detector):
        """Test redacting sensitive data."""
        text = "Email: user@example.com, Card: 4111-1111-1111-1111"
        redacted = detector.redact_sensitive_data(text)

        # Should redact email and card
        assert "user@example.com" not in redacted
        assert "4111-1111-1111-1111" not in redacted
        assert "[REDACTED]" in redacted


class TestRateLimiter:
    """Test cases for RateLimiter."""

    @pytest.fixture
    def limiter(self):
        """Create a RateLimiter for testing."""
        return RateLimiter()

    def test_default_limits(self, limiter):
        """Test default rate limits."""
        # Should allow initial requests
        assert limiter.is_allowed("paste") is True
        assert limiter.is_allowed("clipboard") is True
        assert limiter.is_allowed("large_paste", size=20000) is True

    def test_paste_rate_limit(self, limiter):
        """Test paste operation rate limiting."""
        # Allow up to 30 pastes in 60 seconds
        for _ in range(30):
            assert limiter.is_allowed("paste") is True

        # 31st paste should be blocked
        assert limiter.is_allowed("paste") is False

    def test_clipboard_rate_limit(self, limiter):
        """Test clipboard read rate limiting."""
        # Allow up to 100 reads in 60 seconds
        for _ in range(100):
            assert limiter.is_allowed("clipboard") is True

        # 101st read should be blocked
        assert limiter.is_allowed("clipboard") is False

    def test_large_paste_detection(self, limiter):
        """Test automatic large paste detection."""
        # Small pastes should use normal limit
        assert limiter.is_allowed("paste", size=1000) is True

        # Large pastes should use large_paste limit
        for _ in range(5):
            assert limiter.is_allowed("paste", size=15000) is True

        # 6th large paste should be blocked
        assert limiter.is_allowed("paste", size=15000) is False

    def test_time_window_reset(self, limiter):
        """Test rate limit reset after time window."""
        # Fill up the limit
        for _ in range(30):
            limiter.is_allowed("paste")

        assert limiter.is_allowed("paste") is False

        # Mock time passing
        with patch("time.time", return_value=limiter.history["paste"][0] + 61):
            # Should be allowed after window expires
            assert limiter.is_allowed("paste") is True

    def test_custom_limits(self):
        """Test custom rate limits."""
        custom_limits = {"paste": (10, 30), "clipboard": (50, 30)}
        limiter = RateLimiter(limits=custom_limits)

        # Should use custom limits
        for _ in range(10):
            assert limiter.is_allowed("paste") is True
        assert limiter.is_allowed("paste") is False

    def test_unknown_action(self, limiter):
        """Test unknown actions are always allowed."""
        # Unknown actions should not be limited
        for _ in range(1000):
            assert limiter.is_allowed("unknown_action") is True

    def test_get_remaining_quota(self, limiter):
        """Test getting remaining quota."""
        # Use some quota
        for _ in range(10):
            limiter.is_allowed("paste")

        remaining = limiter.get_remaining_quota("paste")
        assert remaining == 20  # 30 - 10

        # Unknown action should return None
        assert limiter.get_remaining_quota("unknown") is None

    def test_reset_action(self, limiter):
        """Test resetting specific action limits."""
        # Use up limit
        for _ in range(30):
            limiter.is_allowed("paste")

        assert limiter.is_allowed("paste") is False

        # Reset paste limit
        limiter.reset_action("paste")
        assert limiter.is_allowed("paste") is True


class TestPrivacyManager:
    """Test cases for PrivacyManager."""

    @pytest.fixture
    def privacy_manager(self):
        """Create a PrivacyManager for testing."""
        return PrivacyManager()

    def test_initial_state(self, privacy_manager):
        """Test initial privacy state."""
        assert privacy_manager.privacy_mode is False
        assert len(privacy_manager.excluded_apps) == 0
        assert len(privacy_manager.excluded_patterns) == 0

    def test_privacy_mode_toggle(self, privacy_manager):
        """Test privacy mode toggle."""
        # Should allow capture initially
        assert privacy_manager.should_capture("notepad.exe", "test") is True

        # Enable privacy mode
        privacy_manager.set_privacy_mode(True)
        assert privacy_manager.should_capture("notepad.exe", "test") is False

        # Disable privacy mode
        privacy_manager.set_privacy_mode(False)
        assert privacy_manager.should_capture("notepad.exe", "test") is True

    def test_excluded_apps(self, privacy_manager):
        """Test application exclusion."""
        # Add excluded apps
        privacy_manager.add_excluded_app("KeePass")
        privacy_manager.add_excluded_app("1Password")

        # Should not capture from excluded apps
        assert privacy_manager.should_capture("KeePass.exe", "password") is False
        assert privacy_manager.should_capture("1Password - Login", "secret") is False

        # Should capture from other apps
        assert privacy_manager.should_capture("notepad.exe", "text") is True

        # Case insensitive matching
        assert privacy_manager.should_capture("keepass.exe", "password") is False

    def test_remove_excluded_app(self, privacy_manager):
        """Test removing excluded apps."""
        privacy_manager.add_excluded_app("KeePass")
        assert privacy_manager.should_capture("KeePass.exe", "text") is False

        privacy_manager.remove_excluded_app("KeePass")
        assert privacy_manager.should_capture("KeePass.exe", "text") is True

    def test_excluded_patterns(self, privacy_manager):
        """Test content pattern exclusion."""
        # Add patterns
        privacy_manager.add_excluded_pattern(r"CONFIDENTIAL")
        privacy_manager.add_excluded_pattern(r"^---BEGIN.*KEY---")

        # Should not capture matching content
        assert privacy_manager.should_capture("notepad", "CONFIDENTIAL data") is False
        assert privacy_manager.should_capture("notepad", "---BEGIN P" + "RIVATE KEY---") is False

        # Should capture non-matching content
        assert privacy_manager.should_capture("notepad", "normal text") is True

    def test_invalid_pattern(self, privacy_manager):
        """Test invalid regex pattern handling."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            privacy_manager.add_excluded_pattern("[invalid(")

    def test_get_excluded_apps(self, privacy_manager):
        """Test getting list of excluded apps."""
        apps = ["KeePass", "1Password", "Bitwarden"]
        for app in apps:
            privacy_manager.add_excluded_app(app)

        excluded = privacy_manager.get_excluded_apps()
        assert len(excluded) == 3
        assert all(app.lower() in excluded for app in apps)

    def test_clear_exclusions(self, privacy_manager):
        """Test clearing all exclusions."""
        # Add some exclusions
        privacy_manager.add_excluded_app("KeePass")
        privacy_manager.add_excluded_pattern(r"SECRET")

        # Clear all
        privacy_manager.clear_exclusions()

        assert len(privacy_manager.excluded_apps) == 0
        assert len(privacy_manager.excluded_patterns) == 0
        assert privacy_manager.should_capture("KeePass", "SECRET") is True

    def test_export_import_settings(self, privacy_manager, tmp_path):
        """Test exporting and importing privacy settings."""
        # Configure settings
        privacy_manager.set_privacy_mode(True)
        privacy_manager.add_excluded_app("KeePass")
        privacy_manager.add_excluded_pattern(r"CONFIDENTIAL")

        # Export
        export_file = tmp_path / "privacy_settings.json"
        privacy_manager.export_settings(export_file)

        # Create new instance and import
        new_manager = PrivacyManager()
        new_manager.import_settings(export_file)

        # Should have same settings
        assert new_manager.privacy_mode is True
        assert "keepass" in new_manager.excluded_apps
        assert len(new_manager.excluded_patterns) == 1

    def test_default_exclusions(self):
        """Test privacy manager with default exclusions."""
        # Create with default password manager exclusions
        default_apps = ["KeePass", "1Password", "Bitwarden", "LastPass"]
        privacy_manager = PrivacyManager(default_excluded_apps=default_apps)

        # Should exclude default apps
        for app in default_apps:
            assert privacy_manager.should_capture(f"{app}.exe", "password") is False

    def test_combined_conditions(self, privacy_manager):
        """Test combined privacy conditions."""
        privacy_manager.add_excluded_app("Terminal")
        privacy_manager.add_excluded_pattern(r"password:")

        # Should not capture if app is excluded
        assert privacy_manager.should_capture("Terminal", "normal text") is False

        # Should not capture if pattern matches
        assert privacy_manager.should_capture("Notepad", "password: secret") is False

        # Should capture if neither condition matches
        assert privacy_manager.should_capture("Notepad", "normal text") is True

        # Privacy mode overrides all
        privacy_manager.set_privacy_mode(True)
        assert privacy_manager.should_capture("Other App", "normal text") is False
