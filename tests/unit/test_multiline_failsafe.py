"""Test multi-line typing with fail-safe scenarios."""

from unittest.mock import patch

import pytest

from pasta.core.keyboard import PastaKeyboardEngine


class TestMultilineFailsafe:
    """Test multi-line typing with various fail-safe scenarios."""

    @pytest.fixture
    def keyboard_engine(self):
        """Create a keyboard engine instance."""
        return PastaKeyboardEngine()

    def test_multiline_with_failsafe_check(self, keyboard_engine):
        """Test that fail-safe doesn't prevent multi-line typing."""
        test_text = """Line 1
Line 2
Line 3"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Mock position to NOT be at (0,0)
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            assert mock_pyautogui.write.call_count == 3
            assert mock_pyautogui.press.call_count == 2

    def test_multiline_with_failsafe_triggered(self, keyboard_engine):
        """Test multi-line when fail-safe is triggered."""
        test_text = """Line 1
Line 2
Line 3"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Mock position to be at (0,0) - triggers fail-safe
            mock_pyautogui.position.return_value = (0, 0)

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should fail due to fail-safe
            assert result is False
            # Should not complete typing
            assert mock_pyautogui.write.call_count < 3

    def test_multiline_pyautogui_exception(self, keyboard_engine):
        """Test multi-line when pyautogui throws exception."""
        test_text = """Line 1
Line 2
Line 3"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Make press() throw exception on first call
            mock_pyautogui.press.side_effect = Exception("Simulated error")

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should handle exception gracefully
            assert result is False

    def test_multiline_write_exception_on_second_line(self, keyboard_engine):
        """Test when write fails on second line of multi-line text."""
        test_text = """Line 1
Line 2
Line 3"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Make write fail on second call
            call_count = 0

            def write_side_effect(text, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise Exception("Simulated write error")

            mock_pyautogui.write.side_effect = write_side_effect

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should fail gracefully
            assert result is False
            assert call_count == 2  # Failed on second line

    def test_single_vs_multiline_behavior(self, keyboard_engine):
        """Compare single line vs multi-line behavior."""
        single_line = "Single line text"
        multi_line = "Line 1\nLine 2"

        # Test single line
        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(single_line, method="typing")
            assert result is True
            assert mock_pyautogui.write.call_count == 1
            assert mock_pyautogui.press.call_count == 0  # No enter for single line

        # Test multi-line
        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            result = keyboard_engine.paste_text(multi_line, method="typing")
            assert result is True
            assert mock_pyautogui.write.call_count == 2
            assert mock_pyautogui.press.call_count == 1  # One enter between lines

    def test_pyautogui_focus_issue(self, keyboard_engine):
        """Test potential focus issues with pyautogui."""
        test_text = """Line 1
Line 2"""

        with patch("pasta.core.keyboard.pyautogui") as mock_pyautogui:
            # Simulate pyautogui.write returning None (potential focus issue)
            mock_pyautogui.write.return_value = None
            mock_pyautogui.press.return_value = None
            mock_pyautogui.position.return_value = (100, 100)

            result = keyboard_engine.paste_text(test_text, method="typing")

            # Should still succeed
            assert result is True
            assert mock_pyautogui.write.call_count == 2
            assert mock_pyautogui.press.call_count == 1
