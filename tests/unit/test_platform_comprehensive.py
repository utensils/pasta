"""Comprehensive tests for platform utilities to improve coverage."""

import platform
import subprocess
from unittest.mock import Mock, patch

import pytest

from pasta.utils.platform import get_active_window_title, get_paste_key, get_platform, get_platform_info


class TestPlatformUtilities:
    """Test platform utility functions."""

    def test_get_platform(self):
        """Test platform detection."""
        result = get_platform()
        assert result in ["Darwin", "Linux", "Windows"]
        assert result == platform.system()

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_macos(self, mock_get_platform):
        """Test paste key for macOS."""
        mock_get_platform.return_value = "Darwin"
        assert get_paste_key() == "cmd"

    @patch("pasta.utils.platform.get_platform")
    def test_get_paste_key_other(self, mock_get_platform):
        """Test paste key for non-macOS platforms."""
        mock_get_platform.return_value = "Linux"
        assert get_paste_key() == "ctrl"

        mock_get_platform.return_value = "Windows"
        assert get_paste_key() == "ctrl"

    def test_get_platform_info(self):
        """Test platform info retrieval."""
        info = get_platform_info()

        assert isinstance(info, dict)
        assert "system" in info
        assert "release" in info
        assert "version" in info
        assert "machine" in info
        assert "processor" in info
        assert "python_version" in info

        # Verify values match platform module
        assert info["system"] == platform.system()
        assert info["release"] == platform.release()
        assert info["python_version"] == platform.python_version()


class TestGetActiveWindowTitle:
    """Test active window title retrieval across platforms."""

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_macos_success(self, mock_run, mock_get_platform):
        """Test successful window title retrieval on macOS."""
        mock_get_platform.return_value = "Darwin"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Terminal - vim"
        mock_run.return_value = mock_result

        result = get_active_window_title()
        assert result == "Terminal - vim"

        # Verify osascript was called
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "osascript"

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_macos_failure(self, mock_run, mock_get_platform):
        """Test failed window title retrieval on macOS."""
        mock_get_platform.return_value = "Darwin"
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = get_active_window_title()
        assert result == ""

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_macos_exception(self, mock_run, mock_get_platform):
        """Test exception handling on macOS."""
        mock_get_platform.return_value = "Darwin"
        mock_run.side_effect = Exception("Command failed")

        result = get_active_window_title()
        assert result == ""

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_linux_xdotool_success(self, mock_run, mock_get_platform):
        """Test successful window title retrieval on Linux using xdotool."""
        mock_get_platform.return_value = "Linux"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Firefox - GitHub"
        mock_run.return_value = mock_result

        result = get_active_window_title()
        assert result == "Firefox - GitHub"

        # Verify xdotool was called
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "xdotool"

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_linux_wmctrl_fallback(self, mock_run, mock_get_platform):
        """Test Linux fallback to wmctrl when xdotool fails."""
        mock_get_platform.return_value = "Linux"

        # First call (xdotool) fails
        xdotool_result = Mock()
        xdotool_result.returncode = 1

        # Second call (wmctrl) succeeds
        wmctrl_result = Mock()
        wmctrl_result.returncode = 0
        wmctrl_result.stdout = "0x123  0 1234 hostname * Firefox - GitHub\n0x456 0 5678 hostname Terminal"

        mock_run.side_effect = [xdotool_result, wmctrl_result]

        result = get_active_window_title()
        assert result == "* Firefox - GitHub"

        # Verify both commands were tried
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0][0][0][0] == "xdotool"
        assert mock_run.call_args_list[1][0][0][0] == "wmctrl"

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_linux_both_fail(self, mock_run, mock_get_platform):
        """Test Linux when both xdotool and wmctrl fail."""
        mock_get_platform.return_value = "Linux"

        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = get_active_window_title()
        assert result == ""

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_linux_wmctrl_parsing_edge_cases(self, mock_run, mock_get_platform):
        """Test wmctrl output parsing edge cases."""
        mock_get_platform.return_value = "Linux"

        # First call (xdotool) fails
        xdotool_result = Mock()
        xdotool_result.returncode = 1

        # Second call (wmctrl) returns edge case data
        wmctrl_result = Mock()
        wmctrl_result.returncode = 0
        wmctrl_result.stdout = "0x123  0 1234 hostname Terminal\n * short line\n"

        mock_run.side_effect = [xdotool_result, wmctrl_result]

        result = get_active_window_title()
        assert result == ""  # Short line doesn't have enough parts

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    @patch("pasta.utils.platform.get_platform")
    def test_windows_success(self, mock_get_platform):
        """Test successful window title retrieval on Windows."""
        mock_get_platform.return_value = "Windows"

        # Mock ctypes
        with patch("ctypes.windll") as mock_windll:
            mock_user32 = Mock()
            mock_windll.user32 = mock_user32

            mock_user32.GetForegroundWindow.return_value = 12345
            mock_user32.GetWindowTextLengthW.return_value = 10

            # Mock the buffer
            with patch("ctypes.create_unicode_buffer") as mock_buffer:
                mock_buffer_obj = Mock()
                mock_buffer_obj.value = "Notepad"
                mock_buffer.return_value = mock_buffer_obj

                result = get_active_window_title()
                assert result == "Notepad"

    @patch("pasta.utils.platform.get_platform")
    def test_windows_import_error(self, mock_get_platform):
        """Test Windows when ctypes import fails."""
        mock_get_platform.return_value = "Windows"

        # Mock ctypes to raise ImportError
        with patch("ctypes.windll", side_effect=ImportError("No ctypes")):
            result = get_active_window_title()
            assert result == ""

    @patch("pasta.utils.platform.get_platform")
    def test_windows_exception(self, mock_get_platform):
        """Test Windows exception handling."""
        mock_get_platform.return_value = "Windows"

        # Mock ctypes to raise exception
        with patch("ctypes.windll") as mock_windll:
            mock_windll.user32.GetForegroundWindow.side_effect = Exception("Windows API error")

            result = get_active_window_title()
            assert result == ""

    @patch("pasta.utils.platform.get_platform")
    def test_unknown_platform(self, mock_get_platform):
        """Test behavior on unknown platform."""
        mock_get_platform.return_value = "UnknownOS"

        result = get_active_window_title()
        assert result == ""

    @patch("pasta.utils.platform.get_platform")
    @patch("subprocess.run")
    def test_subprocess_timeout(self, mock_run, mock_get_platform):
        """Test subprocess timeout handling."""
        mock_get_platform.return_value = "Darwin"
        mock_run.side_effect = subprocess.TimeoutExpired("osascript", 1)

        result = get_active_window_title()
        assert result == ""
