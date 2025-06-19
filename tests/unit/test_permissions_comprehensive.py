"""Comprehensive tests for permissions module to improve coverage."""

import os
import platform
import subprocess
from unittest.mock import Mock, mock_open, patch

from pasta.utils.permissions import PermissionChecker


class TestPermissionChecker:
    """Test PermissionChecker class."""

    def test_initialization(self):
        """Test PermissionChecker initialization."""
        checker = PermissionChecker()
        assert checker.platform == platform.system()
        assert checker._cached_result is None

    @patch("platform.system")
    def test_check_permissions_caching(self, mock_system):
        """Test permission check result caching."""
        mock_system.return_value = "Windows"
        checker = PermissionChecker()

        # First call
        result1 = checker.check_permissions()
        assert result1 is True

        # Second call should use cache
        result2 = checker.check_permissions()
        assert result2 is True
        assert checker._cached_result is True

    @patch("platform.system")
    def test_check_permissions_unknown_platform(self, mock_system):
        """Test permissions check on unknown platform."""
        mock_system.return_value = "UnknownOS"
        checker = PermissionChecker()

        result = checker.check_permissions()
        assert result is True  # Unknown platforms assumed OK

    @patch("platform.system")
    @patch("subprocess.run")
    def test_macos_accessibility_granted(self, mock_run, mock_system):
        """Test macOS accessibility check when granted."""
        mock_system.return_value = "Darwin"
        mock_result = Mock()
        mock_result.stdout = "true"
        mock_run.return_value = mock_result

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is True
        mock_run.assert_called_once()
        assert "osascript" in mock_run.call_args[0][0]

    @patch("platform.system")
    @patch("subprocess.run")
    def test_macos_accessibility_denied(self, mock_run, mock_system):
        """Test macOS accessibility check when denied."""
        mock_system.return_value = "Darwin"
        mock_result = Mock()
        mock_result.stdout = "false"
        mock_run.return_value = mock_result

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is False

    @patch("platform.system")
    @patch("subprocess.run")
    def test_macos_accessibility_error(self, mock_run, mock_system):
        """Test macOS accessibility check with subprocess error."""
        mock_system.return_value = "Darwin"
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is False

    @patch("platform.system")
    def test_windows_permissions(self, mock_system):
        """Test Windows permissions (always True)."""
        mock_system.return_value = "Windows"
        checker = PermissionChecker()

        result = checker.check_permissions()
        assert result is True

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", False)
    def test_linux_permissions_no_grp_module(self, mock_system):
        """Test Linux permissions when grp module not available."""
        mock_system.return_value = "Linux"
        checker = PermissionChecker()

        result = checker.check_permissions()
        assert result is True  # Can't check without grp

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", True)
    @patch("pasta.utils.permissions.grp")
    @patch("os.getgroups")
    def test_linux_permissions_in_input_group(self, mock_getgroups, mock_grp, mock_system):
        """Test Linux permissions when user is in input group."""
        mock_system.return_value = "Linux"

        # Mock input group
        mock_group = Mock()
        mock_group.gr_gid = 1000
        mock_grp.getgrnam.return_value = mock_group

        # Mock user groups
        mock_getgroups.return_value = [100, 1000, 2000]

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is True
        mock_grp.getgrnam.assert_called_once_with("input")

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", True)
    @patch("pasta.utils.permissions.grp")
    @patch("os.getgroups")
    def test_linux_permissions_not_in_input_group(self, mock_getgroups, mock_grp, mock_system):
        """Test Linux permissions when user is not in input group."""
        mock_system.return_value = "Linux"

        # Mock input group
        mock_group = Mock()
        mock_group.gr_gid = 1000
        mock_grp.getgrnam.return_value = mock_group

        # Mock user groups (without input group)
        mock_getgroups.return_value = [100, 2000]

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is False

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", True)
    @patch("pasta.utils.permissions.grp")
    def test_linux_permissions_no_input_group(self, mock_grp, mock_system):
        """Test Linux permissions when input group doesn't exist."""
        mock_system.return_value = "Linux"
        mock_grp.getgrnam.side_effect = KeyError("input")

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is True  # No input group means not required

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", True)
    @patch("pasta.utils.permissions.grp")
    def test_linux_permissions_exception(self, mock_grp, mock_system):
        """Test Linux permissions with general exception."""
        mock_system.return_value = "Linux"
        mock_grp.getgrnam.side_effect = Exception("Unexpected error")

        checker = PermissionChecker()
        result = checker.check_permissions()

        assert result is True  # On error, assume OK

    @patch("platform.system")
    @patch("pasta.utils.permissions.HAS_GRP", True)
    @patch("pasta.utils.permissions.grp")
    def test_linux_permissions_no_getgroups(self, mock_grp, mock_system):
        """Test Linux permissions when os.getgroups not available."""
        mock_system.return_value = "Linux"

        # Mock input group
        mock_group = Mock()
        mock_group.gr_gid = 1000
        mock_grp.getgrnam.return_value = mock_group

        # Mock os module without getgroups
        with patch("pasta.utils.permissions.os") as mock_os:
            # Remove getgroups attribute
            del mock_os.getgroups

            checker = PermissionChecker()
            result = checker.check_permissions()

            assert result is True  # Can't check without getgroups

    @patch("platform.system")
    @patch("subprocess.run")
    def test_request_macos_permissions(self, mock_run, mock_system):
        """Test requesting macOS permissions."""
        mock_system.return_value = "Darwin"
        checker = PermissionChecker()

        checker.request_permissions()

        mock_run.assert_called_once()
        assert "osascript" in mock_run.call_args[0][0]

    @patch("platform.system")
    @patch("subprocess.run")
    def test_request_macos_permissions_error(self, mock_run, mock_system):
        """Test requesting macOS permissions with error."""
        mock_system.return_value = "Darwin"
        mock_run.side_effect = subprocess.SubprocessError("Failed")

        checker = PermissionChecker()
        # Should not raise exception
        checker.request_permissions()

    @patch("platform.system")
    @patch("builtins.print")
    def test_request_linux_permissions(self, mock_print, mock_system):
        """Test requesting Linux permissions."""
        mock_system.return_value = "Linux"
        checker = PermissionChecker()

        checker.request_permissions()

        # Verify instructions were printed
        assert mock_print.call_count > 0
        printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        assert "sudo usermod" in printed_text

    @patch("platform.system")
    def test_request_windows_permissions(self, mock_system):
        """Test requesting Windows permissions (no-op)."""
        mock_system.return_value = "Windows"
        checker = PermissionChecker()

        # Should do nothing
        checker.request_permissions()

    @patch("platform.system")
    def test_get_permission_error_messages(self, mock_system):
        """Test getting permission error messages for all platforms."""
        # macOS
        mock_system.return_value = "Darwin"
        checker = PermissionChecker()
        msg = checker.get_permission_error_message()
        assert "accessibility permissions" in msg

        # Linux
        mock_system.return_value = "Linux"
        checker = PermissionChecker()
        msg = checker.get_permission_error_message()
        assert "'input' group" in msg

        # Other
        mock_system.return_value = "FreeBSD"
        checker = PermissionChecker()
        msg = checker.get_permission_error_message()
        assert "Permission error" in msg

    @patch("platform.system")
    def test_get_permission_instructions(self, mock_system):
        """Test getting permission instructions for all platforms."""
        # macOS
        mock_system.return_value = "Darwin"
        checker = PermissionChecker()
        instructions = checker.get_permission_instructions()
        assert "Accessibility Setup" in instructions

        # Linux
        mock_system.return_value = "Linux"
        checker = PermissionChecker()
        instructions = checker.get_permission_instructions()
        assert "usermod" in instructions

        # Windows
        mock_system.return_value = "Windows"
        checker = PermissionChecker()
        instructions = checker.get_permission_instructions()
        assert "No special permissions" in instructions

        # Unknown
        mock_system.return_value = "BSD"
        checker = PermissionChecker()
        instructions = checker.get_permission_instructions()
        assert "BSD platform detected" in instructions

    def test_create_info_plist(self):
        """Test Info.plist generation."""
        checker = PermissionChecker()
        plist = checker.create_info_plist()

        assert "<?xml version" in plist
        assert "CFBundleName" in plist
        assert "Pasta" in plist
        assert "NSAccessibilityUsageDescription" in plist

    def test_create_manifest(self):
        """Test Windows manifest generation."""
        checker = PermissionChecker()
        manifest = checker.create_manifest()

        assert "<?xml version" in manifest
        assert "requestedExecutionLevel" in manifest
        assert "asInvoker" in manifest

    @patch("platform.system")
    def test_is_wayland(self, mock_system):
        """Test Wayland detection."""
        # Not Linux
        mock_system.return_value = "Darwin"
        checker = PermissionChecker()
        assert checker.is_wayland() is False

        # Linux with Wayland
        mock_system.return_value = "Linux"
        checker = PermissionChecker()
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}):
            assert checker.is_wayland() is True

        # Linux with X11
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}):
            assert checker.is_wayland() is False

        # Linux with no session type
        with patch.dict(os.environ, {}, clear=True):
            assert checker.is_wayland() is False

    def test_get_linux_setup_script(self):
        """Test Linux setup script generation."""
        checker = PermissionChecker()
        script = checker.get_linux_setup_script()

        assert "#!/bin/bash" in script
        assert "usermod -a -G input" in script
        assert "xdotool" in script
        assert "ydotool" in script

    @patch("platform.system")
    def test_get_linux_distro(self, mock_system):
        """Test Linux distribution detection."""
        # Not Linux
        mock_system.return_value = "Windows"
        checker = PermissionChecker()
        assert checker.get_linux_distro() == ""

        # Linux with os-release
        mock_system.return_value = "Linux"
        checker = PermissionChecker()

        os_release_content = 'NAME="Ubuntu"\nVERSION="22.04"'
        with patch("builtins.open", mock_open(read_data=os_release_content)):
            assert checker.get_linux_distro() == "Ubuntu"

        # Linux without os-release
        with patch("builtins.open", side_effect=FileNotFoundError):
            assert checker.get_linux_distro() == "Unknown"

        # Linux with malformed os-release
        with patch("builtins.open", mock_open(read_data="INVALID FILE")):
            assert checker.get_linux_distro() == "Unknown"
