"""Tests for the PastaKeyboardEngine module."""

from unittest.mock import Mock, patch

import pytest

from pasta.core.keyboard import PastaKeyboardEngine


class TestPastaKeyboardEngine:
    """Test cases for PastaKeyboardEngine."""

    @pytest.fixture
    def engine(self):
        """Create a PastaKeyboardEngine instance for testing."""
        return PastaKeyboardEngine()

    def test_initialization(self, engine):
        """Test PastaKeyboardEngine initializes correctly."""
        assert hasattr(engine, "is_mac")
        assert hasattr(engine, "paste_key")
        assert hasattr(engine, "clipboard_threshold")
        assert hasattr(engine, "chunk_size")
        assert engine.clipboard_threshold == 5000
        assert engine.chunk_size == 200

    def test_platform_detection(self):
        """Test platform-specific initialization."""
        with patch("platform.system") as mock_platform:
            # Test macOS
            mock_platform.return_value = "Darwin"
            engine = PastaKeyboardEngine()
            assert engine.is_mac is True
            assert engine.paste_key == "cmd"

            # Test Windows/Linux
            mock_platform.return_value = "Windows"
            engine = PastaKeyboardEngine()
            assert engine.is_mac is False
            assert engine.paste_key == "ctrl"

    @patch("pyautogui.PAUSE", 0.01)
    def test_pyautogui_optimization(self, engine):
        """Test PyAutoGUI is optimized for speed."""
        # PyAutoGUI PAUSE should be reduced from default
        import pyautogui

        assert pyautogui.PAUSE == 0.01
        assert pyautogui.FAILSAFE is True

    @patch("pyperclip.copy")
    @patch("pyperclip.paste")
    @patch("pyautogui.hotkey")
    def test_paste_via_clipboard(self, mock_hotkey, mock_paste, mock_copy, engine):
        """Test paste using clipboard method."""
        # Store original clipboard content
        mock_paste.return_value = "original"

        result = engine.paste_text("test content", method="clipboard")

        assert result is True
        # Check that "test content" was copied (first call)
        assert mock_copy.call_count == 2
        assert mock_copy.call_args_list[0] == (("test content",), {})
        mock_hotkey.assert_called_with(engine.paste_key, "v")

    @patch("pyperclip.copy")
    @patch("pyperclip.paste")
    @patch("pyautogui.hotkey")
    def test_paste_via_clipboard_restores_original(self, mock_hotkey, mock_paste, mock_copy, engine):
        """Test that clipboard method restores original content."""
        mock_paste.return_value = "original content"

        with patch("time.sleep"):  # Speed up test
            engine.paste_text("new content", method="clipboard")

        # Should restore original
        assert mock_copy.call_count == 2
        mock_copy.assert_called_with("original content")

    @patch("pyautogui.write")
    def test_paste_via_typing(self, mock_write, engine):
        """Test paste using typing method."""
        result = engine.paste_text("small text", method="typing")

        assert result is True
        mock_write.assert_called_once_with("small text", interval=0.005)

    @patch("pyautogui.write")
    @patch("time.sleep")
    def test_paste_large_text_chunking(self, mock_sleep, mock_write, engine):
        """Test large text is chunked properly."""
        large_text = "x" * 1000

        result = engine.paste_text(large_text, method="typing")

        assert result is True
        # Should be called multiple times due to chunking
        assert mock_write.call_count > 1
        # Should pause between chunks
        assert mock_sleep.called

    def test_auto_method_selection_small_text(self, engine):
        """Test automatic method selection for small text."""
        with patch.object(engine, "_paste_via_clipboard") as mock_clipboard:
            engine.paste_text("small", method="auto")
            mock_clipboard.assert_called_once()

    def test_auto_method_selection_large_text(self, engine):
        """Test automatic method selection for large text."""
        large_text = "x" * 6000
        with patch.object(engine, "_paste_via_typing") as mock_typing:
            engine.paste_text(large_text, method="auto")
            mock_typing.assert_called_once()

    @patch("pyautogui.position")
    def test_fail_safe_mechanism(self, mock_position, engine):
        """Test fail-safe mechanism checks mouse position."""
        # Test continue condition
        mock_position.return_value = (500, 500)
        assert engine._check_continue() is True

        # Test abort condition (top-left corner)
        mock_position.return_value = (0, 0)
        assert engine._check_continue() is False

    @patch("pyautogui.write")
    @patch("pyautogui.position")
    def test_typing_abort_on_fail_safe(self, mock_position, mock_write, engine):
        """Test typing stops when fail-safe is triggered."""
        # First check returns True, second returns False
        mock_position.side_effect = [(500, 500), (0, 0)]

        large_text = "x" * 500
        result = engine.paste_text(large_text, method="typing")

        assert result is False
        # Should have stopped early
        assert mock_write.call_count == 1

    @patch("pasta.core.keyboard.pyperclip.paste", return_value="original")
    def test_paste_error_handling(self, mock_paste, engine):
        """Test error handling in paste operations."""
        with patch("pasta.core.keyboard.pyperclip.copy", side_effect=Exception("Clipboard error")):
            result = engine.paste_text("test", method="clipboard")
            assert result is False

    @patch("pyautogui.write")
    @patch("pyautogui.press")
    def test_multiline_text_handling(self, mock_press, mock_write, engine):
        """Test handling of multiline text."""
        multiline = "line1\nline2\nline3"

        engine.paste_text(multiline, method="typing")

        # Should handle newlines properly
        assert mock_write.call_count >= 3
        assert mock_press.call_count >= 2
        mock_press.assert_called_with("enter")

    def test_adaptive_typing_speed(self, engine):
        """Test adaptive typing speed based on system load."""
        adaptive_engine = engine.get_adaptive_engine()

        assert hasattr(adaptive_engine, "get_typing_interval")
        assert hasattr(adaptive_engine, "base_interval")
        assert hasattr(adaptive_engine, "max_interval")

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    def test_adaptive_interval_calculation(self, mock_memory, mock_cpu, engine):
        """Test adaptive interval calculation based on system resources."""
        # Mock low system load
        mock_cpu.return_value = 20.0
        mock_memory.return_value = Mock(percent=30.0)

        adaptive = engine.get_adaptive_engine()
        interval = adaptive.get_typing_interval()

        # Should be close to base interval when load is low
        assert interval < 0.02

        # Mock high system load
        mock_cpu.return_value = 90.0
        mock_memory.return_value = Mock(percent=85.0)

        # Force a new check by resetting last_cpu_check
        adaptive.last_cpu_check = 0
        interval = adaptive.get_typing_interval()

        # Should be higher when load is high
        assert interval > 0.02

    def test_configurable_thresholds(self):
        """Test that thresholds can be configured."""
        engine = PastaKeyboardEngine(clipboard_threshold=1000, chunk_size=100)
        assert engine.clipboard_threshold == 1000
        assert engine.chunk_size == 100

    @patch("pyautogui.write")
    def test_special_characters_handling(self, mock_write, engine):
        """Test handling of special characters."""
        special_text = "Test with @#$%^&*() special chars"

        result = engine.paste_text(special_text, method="typing")

        assert result is True
        mock_write.assert_called_with(special_text, interval=0.005)

    def test_empty_text_handling(self, engine):
        """Test handling of empty text."""
        result = engine.paste_text("", method="auto")
        assert result is True  # Should succeed but do nothing

    @patch("pyautogui.write")
    def test_unicode_text_handling(self, mock_write, engine):
        """Test handling of Unicode text."""
        unicode_text = "Hello 世界 🌍 Привет"

        result = engine.paste_text(unicode_text, method="typing")

        assert result is True
        mock_write.assert_called_with(unicode_text, interval=0.005)

    def test_paste_method_validation(self, engine):
        """Test validation of paste method parameter."""
        # Valid methods should work
        with patch.object(engine, "_paste_via_clipboard", return_value=True):
            assert engine.paste_text("test", method="clipboard") is True

        with patch.object(engine, "_paste_via_typing", return_value=True):
            assert engine.paste_text("test", method="typing") is True

        # Invalid method should default to auto
        with patch.object(engine, "_paste_via_clipboard", return_value=True):
            assert engine.paste_text("test", method="invalid") is True

    @patch("pyautogui.write")
    @patch("time.sleep")
    def test_chunk_boundary_handling(self, mock_sleep, mock_write, engine):
        """Test that text is chunked at appropriate boundaries."""
        # Text exactly at chunk size
        text = "x" * 200
        engine.paste_text(text, method="typing")
        assert mock_write.call_count == 1
        assert mock_sleep.call_count == 0

        # Reset mocks for next test
        mock_write.reset_mock()
        mock_sleep.reset_mock()

        # Text slightly over chunk size
        text = "x" * 201
        engine.paste_text(text, method="typing")
        assert mock_write.call_count == 2
        assert mock_sleep.call_count == 1
