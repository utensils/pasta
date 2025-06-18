"""Tests for keyboard engine multi-line text handling."""

from unittest.mock import patch

import pytest

from pasta.core.keyboard import PastaKeyboardEngine


class TestKeyboardMultiline:
    """Test cases for multi-line text typing."""

    @pytest.fixture
    def keyboard_engine(self):
        """Create a keyboard engine instance."""
        return PastaKeyboardEngine()

    def test_typing_multiline_text(self, keyboard_engine):
        """Test typing multi-line text with proper line breaks."""
        test_text = "First line\nSecond line\nThird line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should have typed each line

            assert mock_pyautogui.write.call_count == 3
            assert mock_pyautogui.press.call_count == 2
            assert result is True

    def test_typing_multiline_with_empty_lines(self, keyboard_engine):
        """Test typing multi-line text with empty lines."""
        test_text = "First line\n\nThird line with empty line above"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle empty lines correctly
            assert mock_pyautogui.press.call_count == 2  # Two enter presses
            assert result is True

    def test_typing_multiline_with_chunks(self, keyboard_engine):
        """Test typing multi-line text that requires chunking."""
        # Create text longer than chunk size (200 chars)
        long_line = "x" * 250  # Longer than chunk size
        test_text = f"Short line\n{long_line}\nAnother short line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should chunk the long line
            assert mock_pyautogui.write.call_count > 3  # More than 3 due to chunking
            assert mock_pyautogui.press.call_count == 2  # Still only 2 line breaks
            assert result is True

    def test_typing_multiline_with_windows_line_endings(self, keyboard_engine):
        """Test typing text with Windows-style line endings."""
        test_text = "First line\r\nSecond line\r\nThird line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle \r\n properly
            assert mock_pyautogui.press.call_count == 2
            assert result is True

    def test_typing_multiline_preserves_indentation(self, keyboard_engine):
        """Test that typing preserves indentation in multi-line text."""
        test_text = "def hello():\n    print('Hello')\n    return True"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Check that indentation is preserved
            calls = mock_pyautogui.write.call_args_list
            assert any("    print('Hello')" in str(call) for call in calls)
            assert any("    return True" in str(call) for call in calls)
            assert result is True

    def test_typing_multiline_with_special_characters(self, keyboard_engine):
        """Test typing multi-line text with special characters."""
        test_text = "Line with émojis 🎉\nLine with symbols: @#$%\nLine with quotes: 'single' \"double\""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle special characters
            assert mock_pyautogui.write.call_count == 3
            assert result is True

    def test_typing_code_block(self, keyboard_engine):
        """Test typing a code block with proper formatting."""
        code_text = """def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

# Test the function
print(factorial(5))"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(code_text, method="typing")

            # Count actual lines
            lines = code_text.split("\n")
            expected_enters = len(lines) - 1

            # Should preserve code structure
            assert mock_pyautogui.press.call_count == expected_enters
            assert result is True

    def test_typing_multiline_abort_between_lines(self, keyboard_engine):
        """Test aborting multi-line typing between lines."""
        test_text = "First line\nSecond line\nThird line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Simulate abort after first line
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:  # After first line
                    keyboard_engine.abort_paste()

            mock_pyautogui.write.side_effect = side_effect

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should have stopped after abort
            assert result is False
            assert mock_pyautogui.write.call_count < 3

    def test_typing_single_line_no_extra_newline(self, keyboard_engine):
        """Test that single line text doesn't add extra newline."""
        test_text = "Single line of text"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should not press enter for single line
            assert mock_pyautogui.write.call_count == 1
            assert mock_pyautogui.press.call_count == 0
            assert result is True

    def test_typing_text_ending_with_newline(self, keyboard_engine):
        """Test typing text that ends with a newline."""
        test_text = "First line\nSecond line\n"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle trailing newline correctly
            # This creates 3 lines: "First line", "Second line", ""
            assert mock_pyautogui.press.call_count == 2
            assert result is True

    def test_typing_large_multiline_text(self, keyboard_engine):
        """Test typing large multi-line text."""
        # Create a large multi-line text
        lines = [f"Line {i}: " + "x" * 100 for i in range(10)]
        test_text = "\n".join(lines)

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle all lines
            assert mock_pyautogui.press.call_count == 9  # 9 line breaks for 10 lines
            assert result is True

    def test_typing_mixed_line_endings(self, keyboard_engine):
        """Test typing text with mixed line endings."""
        test_text = "Unix line\nWindows line\r\nMac classic line\rLast line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should normalize all line endings to \n
            # So we expect 4 lines total, meaning 3 enter presses
            assert mock_pyautogui.press.call_count == 3
            assert mock_pyautogui.write.call_count == 4

            # Verify the text was split correctly
            write_calls = [call.args[0] for call in mock_pyautogui.write.call_args_list]
            assert "Unix line" in write_calls
            assert "Windows line" in write_calls
            assert "Mac classic line" in write_calls
            assert "Last line" in write_calls
            assert result is True

    def test_typing_tabs_and_spaces(self, keyboard_engine):
        """Test typing text with tabs and mixed indentation."""
        test_text = "Line with spaces:    indented\nLine with tab:\tindented\nMixed:\t    both"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(test_text, method="typing")

            # Check that tabs and spaces are preserved
            calls = [call.args[0] for call in mock_pyautogui.write.call_args_list]
            assert any("    indented" in text for text in calls)
            assert any("\tindented" in text for text in calls)
            assert result is True
