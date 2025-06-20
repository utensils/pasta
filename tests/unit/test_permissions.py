"""Tests for the PermissionChecker module."""

import subprocess
import sys
from unittest.mock import Mock, mock_open, patch

import pytest

from pasta.utils.permissions import PermissionChecker


class TestPermissionChecker:
    """Test cases for PermissionChecker."""

    @pytest.fixture
    def checker(self):
        """Create a PermissionChecker instance for testing."""
        return PermissionChecker()

    def test_initialization(self, checker):
        """Test PermissionChecker initializes correctly."""
        assert hasattr(checker, "platform")
        assert checker.platform in ["Darwin", "Windows", "Linux"]

    @patch("platform.system")
    def test_platform_detection(self, mock_system):
        """Test platform detection during initialization."""
        # Test macOS
        mock_system.return_value = "Darwin"
        checker = PermissionChecker()
        assert checker.platform == "Darwin"

        # Test Windows
        mock_system.return_value = "Windows"
        checker = PermissionChecker()
        assert checker.platform == "Windows"

        # Test Linux
        mock_system.return_value = "Linux"
        checker = PermissionChecker()
        assert checker.platform == "Linux"

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_macos_accessibility_check_granted(self, mock_run, mock_system):
        """Test macOS accessibility permission check when granted."""
        # Mock successful accessibility check
        mock_run.return_value = Mock(stdout="true\n", returncode=0)

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        assert result is True
        mock_run.assert_called_once()
        # Verify osascript was called
        assert "osascript" in mock_run.call_args[0][0]

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_macos_accessibility_check_denied(self, mock_run, mock_system):
        """Test macOS accessibility permission check when denied."""
        # Mock failed accessibility check
        mock_run.return_value = Mock(stdout="false\n", returncode=0)

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        assert result is False

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_macos_accessibility_check_error(self, mock_run, mock_system):
        """Test macOS accessibility check with subprocess error."""
        # Mock subprocess error
        mock_run.side_effect = subprocess.SubprocessError("Error")

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        assert result is False

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_macos_request_accessibility(self, mock_run, mock_system):
        """Test requesting accessibility permissions on macOS."""
        checker = PermissionChecker()
        checker.request_permissions()

        mock_run.assert_called_once()
        # Verify System Preferences is opened to accessibility pane
        assert "osascript" in mock_run.call_args[0][0]

    @patch("platform.system", return_value="Windows")
    def test_windows_permission_check(self, mock_system):
        """Test Windows permission check (should always return True)."""
        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        # Windows doesn't require special permissions for our use case
        assert result is True

    @patch("platform.system", return_value="Windows")
    def test_windows_request_permissions(self, mock_system):
        """Test requesting permissions on Windows (no-op)."""
        checker = PermissionChecker()
        # Should not raise exception
        checker.request_permissions()

    @pytest.mark.skipif(sys.platform == "win32", reason="grp module not available on Windows")
    @patch("platform.system", return_value="Linux")
    @patch("os.getgroups")
    @patch("grp.getgrnam")
    def test_linux_input_group_check_member(self, mock_getgrnam, mock_getgroups, mock_system):
        """Test Linux input group check when user is member."""
        # Mock user being in input group
        mock_getgrnam.return_value = Mock(gr_gid=999)
        mock_getgroups.return_value = [100, 999, 1000]  # 999 is input group

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        assert result is True

    @pytest.mark.skipif(sys.platform == "win32", reason="grp module not available on Windows")
    @patch("platform.system", return_value="Linux")
    @patch("os.getgroups")
    @patch("grp.getgrnam")
    def test_linux_input_group_check_not_member(self, mock_getgrnam, mock_getgroups, mock_system):
        """Test Linux input group check when user is not member."""
        # Mock user not being in input group
        mock_getgrnam.return_value = Mock(gr_gid=999)
        mock_getgroups.return_value = [100, 1000]  # 999 not in list

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        assert result is False

    @pytest.mark.skipif(sys.platform == "win32", reason="grp module not available on Windows")
    @patch("platform.system", return_value="Linux")
    @patch("grp.getgrnam")
    def test_linux_input_group_not_exists(self, mock_getgrnam, mock_system):
        """Test Linux when input group doesn't exist."""
        # Mock input group not existing
        mock_getgrnam.side_effect = KeyError("input")

        checker = PermissionChecker()
        checker.clear_cache()  # Clear any cached values
        result = checker.check_permissions()

        # Should return True if group doesn't exist (not required)
        assert result is True

    @patch("platform.system", return_value="Linux")
    def test_linux_request_permissions(self, mock_system):
        """Test requesting permissions on Linux."""
        checker = PermissionChecker()

        with patch("builtins.print") as mock_print:
            checker.request_permissions()

        # Should print instructions
        mock_print.assert_called()

    def test_get_permission_error_message(self, checker):
        """Test getting user-friendly error messages."""
        message = checker.get_permission_error_message()

        assert isinstance(message, str)
        assert len(message) > 0

        # Platform-specific messages
        if checker.platform == "Darwin":
            assert "accessibility" in message.lower()
        elif checker.platform == "Linux":
            assert "input" in message.lower()

    def test_get_permission_instructions(self, checker):
        """Test getting permission setup instructions."""
        instructions = checker.get_permission_instructions()

        assert isinstance(instructions, str)
        assert len(instructions) > 0

        # Should contain platform-specific content
        if checker.platform == "Darwin":
            assert "macOS" in instructions or "Darwin" in instructions
        elif checker.platform == "Linux":
            assert "Linux" in instructions
        elif checker.platform == "Windows":
            assert "Windows" in instructions

    @patch("platform.system", return_value="Darwin")
    def test_macos_create_info_plist(self, mock_system):
        """Test Info.plist generation for macOS."""
        checker = PermissionChecker()
        plist_content = checker.create_info_plist()

        assert isinstance(plist_content, str)
        assert "NSAccessibilityUsageDescription" in plist_content
        assert "com.yourcompany.pasta" in plist_content

    @patch("platform.system", return_value="Windows")
    def test_windows_create_manifest(self, mock_system):
        """Test manifest generation for Windows."""
        checker = PermissionChecker()
        manifest_content = checker.create_manifest()

        assert isinstance(manifest_content, str)
        assert "requestedExecutionLevel" in manifest_content
        assert "asInvoker" in manifest_content

    @patch("platform.system", return_value="Linux")
    @patch("os.environ")
    def test_linux_detect_wayland(self, mock_environ, mock_system):
        """Test Wayland detection on Linux."""
        mock_environ.get.return_value = "wayland"

        checker = PermissionChecker()
        is_wayland = checker.is_wayland()

        assert is_wayland is True

        # Test X11
        mock_environ.get.return_value = "x11"
        is_wayland = checker.is_wayland()
        assert is_wayland is False

    @patch("platform.system", return_value="Linux")
    def test_linux_get_setup_script(self, mock_system):
        """Test Linux setup script generation."""
        checker = PermissionChecker()
        script = checker.get_linux_setup_script()

        assert isinstance(script, str)
        assert "usermod -a -G input" in script
        assert "#!/bin/bash" in script

    def test_fallback_behavior(self, checker):
        """Test fallback behavior for unknown platforms."""
        with patch.object(checker, "platform", "Unknown"):
            checker.clear_cache()  # Clear any cached values
            # Should not crash
            result = checker.check_permissions()
            assert result is True  # Default to True for unknown platforms

            # Request should be no-op
            checker.request_permissions()

    @patch("platform.system", return_value="Darwin")
    @patch("subprocess.run")
    def test_macos_permission_caching(self, mock_run, mock_system):
        """Test permission result caching on macOS."""
        mock_run.return_value = Mock(stdout="true\n", returncode=0)

        checker = PermissionChecker()
        checker.clear_cache()  # Ensure we start with no cache

        # First call
        result1 = checker.check_permissions()
        assert result1 is True
        assert mock_run.call_count == 1

        # Second call should use cache
        result2 = checker.check_permissions()
        assert result2 is True
        assert mock_run.call_count == 1  # Not called again

    def test_permission_check_thread_safety(self, checker):
        """Test that permission checking is thread-safe."""
        # Verify thread safety mechanisms exist
        assert hasattr(checker, "_check_lock") or hasattr(checker, "_permission_lock")

    @patch("platform.system", return_value="Linux")
    @patch("builtins.open", new_callable=mock_open, read_data="Linux")
    def test_linux_distro_detection(self, mock_file, mock_system):
        """Test Linux distribution detection."""
        checker = PermissionChecker()
        distro = checker.get_linux_distro()

        assert isinstance(distro, str)
        assert len(distro) > 0
