"""Tests for the platform utility module."""

from unittest.mock import patch

from pasta.utils.platform import get_paste_key, get_platform, get_platform_info


class TestPlatform:
    """Test cases for platform detection utilities."""

    def test_get_platform_returns_string(self):
        """Test that get_platform returns a string."""
        result = get_platform()
        assert isinstance(result, str)
        assert result in ["Darwin", "Windows", "Linux", "Java", ""]  # Common platform values

    @patch("platform.system")
    def test_get_platform_darwin(self, mock_system):
        """Test get_platform on macOS."""
        mock_system.return_value = "Darwin"
        assert get_platform() == "Darwin"

    @patch("platform.system")
    def test_get_platform_windows(self, mock_system):
        """Test get_platform on Windows."""
        mock_system.return_value = "Windows"
        assert get_platform() == "Windows"

    @patch("platform.system")
    def test_get_platform_linux(self, mock_system):
        """Test get_platform on Linux."""
        mock_system.return_value = "Linux"
        assert get_platform() == "Linux"

    def test_get_paste_key_default(self):
        """Test get_paste_key returns valid modifier."""
        key = get_paste_key()
        assert key in ["cmd", "ctrl"]

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_macos(self, mock_get_platform):
        """Test get_paste_key returns 'cmd' on macOS."""
        mock_get_platform.return_value = "Darwin"
        assert get_paste_key() == "cmd"

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_windows(self, mock_get_platform):
        """Test get_paste_key returns 'ctrl' on Windows."""
        mock_get_platform.return_value = "Windows"
        assert get_paste_key() == "ctrl"

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_linux(self, mock_get_platform):
        """Test get_paste_key returns 'ctrl' on Linux."""
        mock_get_platform.return_value = "Linux"
        assert get_paste_key() == "ctrl"

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_unknown(self, mock_get_platform):
        """Test get_paste_key returns 'ctrl' for unknown platforms."""
        mock_get_platform.return_value = "FreeBSD"
        assert get_paste_key() == "ctrl"

    def test_get_platform_info_structure(self):
        """Test get_platform_info returns expected structure."""
        info = get_platform_info()

        # Check that all expected keys are present
        expected_keys = ["system", "release", "version", "machine", "processor", "python_version"]
        for key in expected_keys:
            assert key in info

        # Check that all values are strings
        for value in info.values():
            assert isinstance(value, str)

    @patch("platform.system", return_value="TestOS")
    @patch("platform.release", return_value="1.0")
    @patch("platform.version", return_value="1.0.0")
    @patch("platform.machine", return_value="x86_64")
    @patch("platform.processor", return_value="Intel")
    @patch("platform.python_version", return_value="3.9.0")
    def test_get_platform_info_mocked(self, *mocks):
        """Test get_platform_info with mocked values."""
        info = get_platform_info()

        assert info["system"] == "TestOS"
        assert info["release"] == "1.0"
        assert info["version"] == "1.0.0"
        assert info["machine"] == "x86_64"
        assert info["processor"] == "Intel"
        assert info["python_version"] == "3.9.0"

    def test_get_platform_consistency(self):
        """Test that multiple calls to get_platform return the same value."""
        first_call = get_platform()
        second_call = get_platform()
        assert first_call == second_call

    def test_platform_specific_behavior(self):
        """Test platform-specific behavior is consistent."""
        current_platform = get_platform()
        paste_key = get_paste_key()

        if current_platform == "Darwin":
            assert paste_key == "cmd"
        else:
            assert paste_key == "ctrl"
