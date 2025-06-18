"""Test multi-line behavior in app context."""

from unittest.mock import MagicMock, patch

import pytest

from pasta.core.keyboard import PastaKeyboardEngine


class TestMultilineAppBehavior:
    """Test multi-line typing behavior that matches app usage."""

    @pytest.fixture
    def keyboard_engine(self):
        """Create a keyboard engine instance."""
        return PastaKeyboardEngine()

    def test_multiline_with_initial_delay(self, keyboard_engine):
        """Test that multi-line text has initial delay."""
        test_text = """Lorem ipsum dolor sit amet
Consectetur adipiscing elit
Sed do eiusmod tempor"""

        with (
            patch("pasta.core.keyboard.pyautogui") as mock_pyautogui,
            patch("pasta.core.keyboard.time.sleep") as mock_sleep,
        ):
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            # Should have initial delay for multi-line
            mock_sleep.assert_any_call(0.2)

    def test_single_line_no_initial_delay(self, keyboard_engine):
        """Test that single line has no initial delay."""
        test_text = "Lorem ipsum dolor sit amet"

        with (
            patch("pasta.core.keyboard.pyautogui") as mock_pyautogui,
            patch("pasta.core.keyboard.time.sleep") as mock_sleep,
        ):
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            # Should not have 0.1s delay for single line
            if mock_sleep.called:
                # Only chunk delays should be present
                for call in mock_sleep.call_args_list:
                    assert call[0][0] != 0.2

    def test_pyautogui_permissions_issue(self, keyboard_engine):
        """Test when pyautogui might have permission issues."""
        test_text = """Line 1
Line 2"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Simulate pyautogui failing silently
            mock_pyautogui.write = MagicMock(return_value=None)
            mock_pyautogui.press = MagicMock(return_value=None)
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should still return True (no exception)
            assert result is True
            assert mock_pyautogui.write.called
            assert mock_pyautogui.press.called

    def test_app_context_simulation(self, keyboard_engine):
        """Simulate app context where multi-line might fail."""
        test_text = """Lorem ipsum dolor sit amet
Consectetur adipiscing elit
Sed do eiusmod tempor"""

        # Track actual calls
        write_calls = []
        press_calls = []

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            mock_pyautogui.write.side_effect = lambda text, **kwargs: write_calls.append(text)
            mock_pyautogui.press.side_effect = lambda key: press_calls.append(key)
            mock_pyautogui.position.return_value = (100, 100)

            # Simulate being called from app context
            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            assert len(write_calls) == 3  # Three lines
            assert len(press_calls) == 2  # Two enters

            # Verify content
            assert "Lorem ipsum dolor sit amet" in write_calls
            assert "Consectetur adipiscing elit" in write_calls
            assert "Sed do eiusmod tempor" in write_calls

    def test_empty_lines_in_multiline(self, keyboard_engine):
        """Test multi-line with empty lines."""
        test_text = """First line

Third line"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            # Empty line should still trigger enter
            assert mock_pyautogui.press.call_count == 2

    def test_very_long_multiline(self, keyboard_engine):
        """Test multi-line with very long lines that need chunking."""
        long_line = "x" * 250  # Longer than chunk size
        test_text = f"Short line\n{long_line}\nAnother short line"

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            # Should have more write calls due to chunking
            assert mock_pyautogui.write.call_count > 3
            assert mock_pyautogui.press.call_count == 2  # Still only 2 enters
