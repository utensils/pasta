"""Additional tests for PermissionChecker to improve coverage."""

import platform
from unittest.mock import Mock, patch

import pytest

from pasta.utils.permissions import PermissionChecker


class TestPermissionCheckerCoverage:
    """Additional test cases for PermissionChecker coverage."""

    @pytest.fixture
    def checker(self):
        """Create a PermissionChecker instance for testing."""
        return PermissionChecker()

    def test_cached_result(self, checker):
        """Test that permission check results are cached."""
        # Mock platform check
        with patch.object(checker, "_check_macos_accessibility", return_value=True) as mock_check:
            checker.platform = "Darwin"

            # First call should check
            result1 = checker.check_permissions()
            assert result1 is True
            mock_check.assert_called_once()

            # Second call should use cache
            result2 = checker.check_permissions()
            assert result2 is True
            # Should still only be called once
            mock_check.assert_called_once()

    @pytest.mark.skipif(platform.system() == "Windows", reason="os.getuid doesn't exist on Windows")
    @patch("platform.system", return_value="Linux")
    @patch("os.getuid", return_value=1000)  # Non-root user
    def test_linux_permission_denied(self, mock_uid, mock_system):
        """Test Linux permissions when not running as root."""
        checker = PermissionChecker()

        with patch.object(checker, "_check_linux_permissions", return_value=False):
            result = checker.check_permissions()
            assert result is False

    @patch("platform.system", return_value="Unknown")
    def test_unknown_platform(self, mock_system):
        """Test permissions on unknown platform."""
        checker = PermissionChecker()
        result = checker.check_permissions()
        # Unknown platforms should return True
        assert result is True

    @patch("platform.system", return_value="Darwin")
    def test_request_permissions_macos(self, mock_system):
        """Test requesting permissions on macOS."""
        checker = PermissionChecker()

        # Test when subprocess succeeds
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            # request_permissions returns None, not boolean
            result = checker.request_permissions()
            assert result is None
            mock_run.assert_called_once()

    @patch("platform.system", return_value="Windows")
    def test_request_permissions_windows(self, mock_system):
        """Test requesting permissions on Windows."""
        checker = PermissionChecker()

        # request_permissions returns None for Windows
        result = checker.request_permissions()
        assert result is None

    @patch("platform.system", return_value="Linux")
    def test_request_permissions_linux(self, mock_system, capsys):
        """Test requesting permissions on Linux."""
        checker = PermissionChecker()

        # request_permissions returns None and prints instructions
        result = checker.request_permissions()
        assert result is None

        # Check that instructions were printed
        captured = capsys.readouterr()
        assert "sudo usermod -a -G input $USER" in captured.out

    @patch("platform.system", return_value="Unknown")
    def test_request_permissions_unknown(self, mock_system):
        """Test requesting permissions on unknown platform."""
        checker = PermissionChecker()
        # request_permissions returns None for unknown platforms
        result = checker.request_permissions()
        assert result is None

    def test_thread_safety(self, checker):
        """Test thread safety of permission checking."""
        import threading

        results = []

        def check_permissions():
            result = checker.check_permissions()
            results.append(result)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=check_permissions)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All results should be the same
        assert len(set(results)) == 1
