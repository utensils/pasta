"""Comprehensive tests for keyboard module to improve coverage."""

import threading
import time
from unittest.mock import Mock, patch

from pasta.core.keyboard import AdaptiveTypingEngine, PastaKeyboardEngine


class TestAdaptiveTypingEngineExtended:
    """Extended tests for AdaptiveTypingEngine to cover edge cases."""

    @patch("time.time")
    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    def test_get_typing_interval_cached_result(self, mock_memory, mock_cpu, mock_time):
        """Test that typing interval uses cached value within 2 seconds."""
        engine = AdaptiveTypingEngine()

        # First call - should check CPU
        mock_time.return_value = 1000.0
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(percent=60.0)

        interval1 = engine.get_typing_interval()

        # Verify CPU was checked
        mock_cpu.assert_called_once()
        mock_memory.assert_called_once()

        # Second call within 2 seconds - should use cache
        mock_time.return_value = 1001.0  # 1 second later
        mock_cpu.reset_mock()
        mock_memory.reset_mock()

        interval2 = engine.get_typing_interval()

        # Should return base interval without checking CPU
        assert interval2 == engine.base_interval
        mock_cpu.assert_not_called()
        mock_memory.assert_not_called()

        # Third call after 2 seconds - should check CPU again
        mock_time.return_value = 1003.0  # 3 seconds after first call
        mock_cpu.return_value = 80.0
        mock_memory.return_value = Mock(percent=90.0)

        interval3 = engine.get_typing_interval()

        # Verify CPU was checked again
        mock_cpu.assert_called_once()
        mock_memory.assert_called_once()
        assert interval3 > interval1  # Higher stress = longer interval


class TestPastaKeyboardEngineExtended:
    """Extended tests for PastaKeyboardEngine to cover edge cases."""

    def test_paste_via_clipboard_keyboard_interrupt(self):
        """Test clipboard paste handling KeyboardInterrupt."""
        engine = PastaKeyboardEngine()

        with patch("pyperclip.paste", return_value="original"), patch("pyperclip.copy", side_effect=KeyboardInterrupt()):
            result = engine.paste_text("test", method="clipboard")
            assert result is False

    def test_paste_via_typing_abort_event_with_callback(self):
        """Test typing paste with abort event and callback."""
        engine = PastaKeyboardEngine()

        # Set up abort callback
        callback_called = []
        engine._abort_callback = lambda: callback_called.append(True)

        # Track write calls to set abort event after first call
        write_count = [0]

        def mock_write(*args, **kwargs):
            write_count[0] += 1
            if write_count[0] == 1:
                # Set abort event after first chunk
                engine._abort_event.set()

        with patch("pyautogui.write", side_effect=mock_write), patch("pyautogui.position", return_value=(100, 100)):
            result = engine.paste_text("test text", method="typing")

        # Since abort happens during typing, result should be False
        assert result is False
        # Callback should be called when abort is detected
        assert len(callback_called) == 1

    def test_paste_via_typing_abort_during_multiline(self):
        """Test abort during multiline typing."""
        engine = PastaKeyboardEngine()

        # Text with multiple lines
        text = "Line 1\nLine 2\nLine 3"

        # Track what was typed
        typed_chunks = []

        def mock_write(text, interval=0):
            typed_chunks.append(text)
            # Set abort event after first line
            if len(typed_chunks) == 1:
                engine._abort_event.set()

        with (
            patch("pyautogui.write", side_effect=mock_write),
            patch("pyautogui.press"),
            patch("pyautogui.position", return_value=(100, 100)),
        ):
            result = engine.paste_text(text, method="typing")

        assert result is False
        assert len(typed_chunks) == 1  # Should stop after first chunk

        # Reset abort event
        engine._abort_event.clear()

    def test_paste_via_typing_abort_after_chunk(self):
        """Test abort check after typing a chunk."""
        engine = PastaKeyboardEngine()

        # Large text that will be chunked
        text = "X" * 300  # Larger than chunk size (200)

        # Track what was typed
        typed_chunks = []
        callback_called = []

        engine._abort_callback = lambda: callback_called.append(True)

        def mock_write(text, interval=0):
            typed_chunks.append(text)
            # Set abort event after first chunk
            if len(typed_chunks) == 1:
                engine._abort_event.set()

        with patch("pyautogui.write", side_effect=mock_write), patch("pyautogui.position", return_value=(100, 100)):
            result = engine.paste_text(text, method="typing")

        assert result is False
        assert len(typed_chunks) == 1  # Should stop after first chunk
        assert len(callback_called) == 1  # Callback should be called

        # Reset abort event
        engine._abort_event.clear()
        engine._abort_callback = None

    def test_paste_via_typing_fail_safe_triggered(self):
        """Test typing paste when fail-safe is triggered."""
        engine = PastaKeyboardEngine()

        # Mock mouse position to trigger fail-safe
        with patch("pyautogui.position", return_value=(0, 0)), patch("pyautogui.write") as mock_write:
            result = engine.paste_text("test", method="typing")

        assert result is False
        mock_write.assert_not_called()  # Should not type anything

    def test_paste_via_typing_keyboard_interrupt(self):
        """Test typing paste handling KeyboardInterrupt."""
        engine = PastaKeyboardEngine()

        with patch("pyautogui.write", side_effect=KeyboardInterrupt()):
            result = engine.paste_text("test", method="typing")
            assert result is False

    def test_paste_via_typing_general_exception(self):
        """Test typing paste handling general exceptions."""
        engine = PastaKeyboardEngine()

        with patch("pyautogui.write", side_effect=Exception("Unexpected error")):
            result = engine.paste_text("test", method="typing")
            assert result is False

    def test_check_continue_exception_handling(self):
        """Test _check_continue exception handling."""
        engine = PastaKeyboardEngine()

        with patch("pyautogui.position", side_effect=Exception("Position error")):
            # Should return True (continue) on error
            assert engine._check_continue() is True

    def test_abort_paste_while_pasting(self):
        """Test aborting paste operation while it's running."""
        engine = PastaKeyboardEngine()

        # Set up a callback
        callback_called = []
        engine._abort_callback = lambda: callback_called.append(True)

        # Use an event to signal when pasting has started
        paste_started = threading.Event()

        # Start a paste in another thread
        def paste_worker():
            with patch("pyautogui.write") as mock_write, patch("pyautogui.position", return_value=(100, 100)):
                # Make write slow so we can abort it
                def slow_write(t, i):
                    paste_started.set()  # Signal that we've started
                    time.sleep(0.1)

                mock_write.side_effect = slow_write
                engine.paste_text("X" * 1000, method="typing")

        paste_thread = threading.Thread(target=paste_worker)
        paste_thread.start()

        # Wait for paste to actually start
        paste_started.wait(timeout=1.0)

        # Now abort the paste
        engine.abort_paste()

        # Wait for thread to finish
        paste_thread.join(timeout=1.0)

        # Verify abort worked
        assert engine._abort_event.is_set()
        assert engine.is_pasting() is False
        assert len(callback_called) >= 1  # May be called multiple times

        # Reset
        engine._abort_event.clear()
        engine._abort_callback = None

    def test_paste_empty_text(self):
        """Test pasting empty text."""
        engine = PastaKeyboardEngine()

        # Empty text should return True immediately
        result = engine.paste_text("", method="typing")
        assert result is True

        result = engine.paste_text("", method="clipboard")
        assert result is True

    def test_paste_invalid_method_defaults_to_auto(self):
        """Test that invalid paste method defaults to auto selection."""
        engine = PastaKeyboardEngine()

        with patch("pyperclip.copy"), patch("pyperclip.paste", return_value=""), patch("pyautogui.hotkey"):
            # Small text with invalid method should use clipboard
            result = engine.paste_text("small", method="invalid")
            assert result is True

    def test_multiline_with_different_line_endings(self):
        """Test handling different line ending formats."""
        engine = PastaKeyboardEngine()

        # Test Windows line endings
        text_crlf = "Line 1\r\nLine 2\r\nLine 3"
        typed_lines = []

        def track_write(text, interval=0):
            typed_lines.append(text)

        with (
            patch("pyautogui.write", side_effect=track_write),
            patch("pyautogui.press"),
            patch("pyautogui.position", return_value=(100, 100)),
        ):
            engine.paste_text(text_crlf, method="typing")

        assert "Line 1" in typed_lines[0]
        assert "Line 2" in typed_lines[1]
        assert "Line 3" in typed_lines[2]

        # Test old Mac line endings
        typed_lines.clear()
        text_cr = "Line 1\rLine 2\rLine 3"

        with (
            patch("pyautogui.write", side_effect=track_write),
            patch("pyautogui.press"),
            patch("pyautogui.position", return_value=(100, 100)),
        ):
            engine.paste_text(text_cr, method="typing")

        assert "Line 1" in typed_lines[0]
        assert "Line 2" in typed_lines[1]
        assert "Line 3" in typed_lines[2]

    def test_get_adaptive_engine(self):
        """Test getting the adaptive engine instance."""
        engine = PastaKeyboardEngine()
        adaptive = engine.get_adaptive_engine()

        assert isinstance(adaptive, AdaptiveTypingEngine)
        assert adaptive is engine._adaptive_engine  # Should be same instance

    def test_concurrent_paste_operations(self):
        """Test thread safety of paste operations."""
        # Create separate engine instances for true concurrent testing
        engines = [PastaKeyboardEngine() for _ in range(5)]
        results = []
        results_lock = threading.Lock()

        def paste_worker(engine, text, method):
            with (
                patch("pyautogui.write"),
                patch("pyautogui.position", return_value=(100, 100)),
                patch("pyperclip.copy"),
                patch("pyperclip.paste", return_value=""),
                patch("pyautogui.hotkey"),
            ):
                result = engine.paste_text(text, method)
                with results_lock:
                    results.append(result)

        # Start multiple paste operations with separate engines
        threads = []
        for i in range(5):
            method = "typing" if i % 2 == 0 else "clipboard"
            t = threading.Thread(target=paste_worker, args=(engines[i], f"Text {i}", method))
            threads.append(t)
            t.start()

        # Wait for all to complete with timeout
        for t in threads:
            t.join(timeout=5.0)

        # All should complete successfully with separate engines
        assert len(results) == 5
        assert all(results)
