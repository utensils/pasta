"""Tests for typing in app context."""

import threading
import time

from pasta.core.keyboard import PastaKeyboardEngine


class TestAppContextTyping:
    """Test typing behavior in app context."""

    def test_typing_from_different_thread(self):
        """Test that typing works when called from a different thread."""
        engine = PastaKeyboardEngine()
        test_text = """Lorem ipsum dolor sit amet
Consectetur adipiscing elit
Sed do eiusmod tempor"""

        result = None
        calls = []

        # Mock the engine's _ensure_pyautogui method before thread starts
        from unittest.mock import Mock

        mock_pyautogui = Mock()
        mock_pyautogui.write.side_effect = lambda text, **kwargs: calls.append(("write", text))
        mock_pyautogui.press.side_effect = lambda key: calls.append(("press", key))
        mock_pyautogui.position.return_value = (100, 100)  # Not at fail-safe position
        engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

        def run_in_thread():
            nonlocal result
            result = engine.paste_text(test_text, method="typing")

        # Run in separate thread like the app does
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=5)

        assert result is True
        assert len(calls) > 0
        assert any(call[0] == "write" for call in calls)
        assert any(call[0] == "press" for call in calls)

    def test_timing_delay_issue(self):
        """Test if timing delays might be causing issues."""
        engine = PastaKeyboardEngine()
        test_text = "Lorem ipsum dolor sit amet"

        # Test with different timing
        from unittest.mock import Mock

        mock_pyautogui = Mock()
        mock_pyautogui.position.return_value = (100, 100)
        engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

        result = engine.paste_text(test_text, method="typing")
        assert result is True
        mock_pyautogui.write.assert_called()

    def test_focus_and_timing_issues(self):
        """Test potential focus and timing issues."""
        engine = PastaKeyboardEngine()
        test_text = "Test text with multiple words"

        # Simulate focus issues by making first write fail
        call_count = 0

        def write_side_effect(text, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Simulate focus not ready
                time.sleep(0.1)
            return None

        from unittest.mock import Mock

        mock_pyautogui = Mock()
        mock_pyautogui.write.side_effect = write_side_effect
        mock_pyautogui.position.return_value = (100, 100)
        engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

        result = engine.paste_text(test_text, method="typing")

        assert result is True
        assert call_count == 1  # Should have been called

    def test_empty_content_handling(self):
        """Test handling of empty or None content."""
        from unittest.mock import Mock

        # Test empty string
        engine = PastaKeyboardEngine()
        mock_pyautogui = Mock()
        engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

        result = engine.paste_text("", method="typing")
        assert result is True
        mock_pyautogui.write.assert_not_called()

        # Test None (though this should be caught earlier)
        engine2 = PastaKeyboardEngine()
        mock_pyautogui2 = Mock()
        engine2._ensure_pyautogui = Mock(return_value=mock_pyautogui2)

        result = engine2.paste_text(None, method="typing")
        assert result is True
        mock_pyautogui2.write.assert_not_called()

    def test_special_characters_in_context(self):
        """Test special characters that might cause issues."""
        from unittest.mock import Mock

        test_texts = [
            "Text with colon: like this",
            "Text with dots... multiple dots",
            "Numbers 1.1. 1.2. 1.3.",
            "Special chars @#$%^&*()",
        ]

        for text in test_texts:
            engine = PastaKeyboardEngine()
            mock_pyautogui = Mock()
            mock_pyautogui.position.return_value = (100, 100)
            engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

            result = engine.paste_text(text, method="typing")
            assert result is True
            mock_pyautogui.write.assert_called()

    def test_fail_safe_disabled_check(self):
        """Check if fail-safe might be preventing typing."""
        engine = PastaKeyboardEngine()
        test_text = "Test text"

        from unittest.mock import Mock

        mock_pyautogui = Mock()
        # Mock the position to be at (0, 0) which triggers fail-safe
        mock_pyautogui.position.return_value = (0, 0)
        engine._ensure_pyautogui = Mock(return_value=mock_pyautogui)

        result = engine.paste_text(test_text, method="typing")

        # Should fail due to fail-safe
        assert result is False
        mock_pyautogui.write.assert_not_called()
