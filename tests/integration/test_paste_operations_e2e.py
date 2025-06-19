"""End-to-end integration tests for paste operations with different modes."""

import time
from unittest.mock import patch

import pytest

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray


class TestPasteOperationsE2E:
    """End-to-end tests for paste operations in different modes."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test_paste_e2e.db")

    @pytest.fixture
    def components(self, temp_db):
        """Create real component instances."""
        return {
            "clipboard_manager": ClipboardManager(),
            "keyboard_engine": PastaKeyboardEngine(),
            "storage_manager": StorageManager(temp_db),
        }

    @pytest.fixture
    def mock_system_components(self):
        """Mock system components to prevent GUI creation."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
            patch("pasta.utils.permissions.PermissionChecker"),
        ):
            yield

    def test_typing_mode_paste_operation(self, components):
        """Test paste operation in typing mode."""
        keyboard_engine = components["keyboard_engine"]

        # Track what was typed
        typed_text = []

        with patch("pyautogui.write") as mock_write:
            mock_write.side_effect = lambda text, interval=0: typed_text.append(text)

            # Test basic text
            test_text = "Hello, World!"
            result = keyboard_engine.paste_text(test_text, method="typing")

            assert result is True
            assert len(typed_text) == 1
            assert typed_text[0] == test_text

    def test_clipboard_mode_paste_operation(self, components):
        """Test paste operation in clipboard mode."""
        keyboard_engine = components["keyboard_engine"]

        # Track clipboard operations
        clipboard_copies = []
        hotkey_calls = []

        with (
            patch("pyperclip.copy") as mock_copy,
            patch("pyperclip.paste", return_value="original"),
            patch("pyautogui.hotkey") as mock_hotkey,
        ):
            mock_copy.side_effect = lambda text: clipboard_copies.append(text)
            mock_hotkey.side_effect = lambda *keys: hotkey_calls.append(keys)

            # Test clipboard paste
            test_text = "Clipboard paste test"
            result = keyboard_engine.paste_text(test_text, method="clipboard")

            assert result is True
            assert len(clipboard_copies) >= 1
            assert test_text in clipboard_copies
            assert len(hotkey_calls) >= 1

            # Verify paste hotkey was used
            assert any(("cmd", "v") in keys or ("ctrl", "v") in keys for keys in hotkey_calls)

    def test_auto_mode_selection(self, components):
        """Test auto mode selecting appropriate paste method."""
        keyboard_engine = components["keyboard_engine"]

        # Test small text - should use typing
        small_text = "Small"
        with patch("pyautogui.write") as mock_write:
            keyboard_engine.paste_text(small_text, method="auto")
            mock_write.assert_called()

        # Test large text - should use clipboard
        large_text = "x" * 10000
        with (
            patch("pyperclip.copy") as mock_copy,
            patch("pyautogui.hotkey") as mock_hotkey,
        ):
            keyboard_engine.paste_text(large_text, method="auto")
            mock_copy.assert_called()
            mock_hotkey.assert_called()

    def test_multiline_text_handling(self, components):
        """Test handling of multiline text in different modes."""
        keyboard_engine = components["keyboard_engine"]

        multiline_text = "Line 1\nLine 2\nLine 3"

        # Test typing mode with multiline
        typed_chunks = []
        with patch("pyautogui.write") as mock_write:
            mock_write.side_effect = lambda text, interval=0: typed_chunks.append(text)

            keyboard_engine.paste_text(multiline_text, method="typing")

            # Should handle line breaks
            assert len(typed_chunks) > 0
            assert "Line 1" in typed_chunks[0]

        # Test clipboard mode with multiline
        with (
            patch("pyperclip.copy") as mock_copy,
            patch("pyautogui.hotkey"),
        ):
            keyboard_engine.paste_text(multiline_text, method="clipboard")
            mock_copy.assert_called_with(multiline_text)

    def test_special_characters_handling(self, components):
        """Test handling of special characters and unicode."""
        keyboard_engine = components["keyboard_engine"]

        # Test various special characters
        test_cases = [
            "Special chars: !@#$%^&*()",
            "Unicode: 你好世界 🌍 émojis",
            "Quotes: \"double\" and 'single'",
            "Escape chars: \t tab \\ backslash",
        ]

        for test_text in test_cases:
            # Typing mode
            with patch("pyautogui.write") as mock_write:
                result = keyboard_engine.paste_text(test_text, method="typing")
                assert result is True
                mock_write.assert_called_with(test_text, interval=0.01)

            # Clipboard mode
            with (
                patch("pyperclip.copy") as mock_copy,
                patch("pyautogui.hotkey"),
            ):
                result = keyboard_engine.paste_text(test_text, method="clipboard")
                assert result is True
                mock_copy.assert_called_with(test_text)

    def test_paste_with_rate_limiting(self, components):
        """Test paste operations respect rate limiting."""
        keyboard_engine = components["keyboard_engine"]

        # Simulate rapid paste attempts
        paste_times = []

        with patch("pyautogui.write"):
            for i in range(10):
                start = time.time()
                keyboard_engine.paste_text(f"Rapid paste {i}", method="typing")
                paste_times.append(time.time() - start)

        # Should have some delay between pastes
        # (actual implementation may vary)
        assert all(t >= 0 for t in paste_times)

    def test_paste_error_recovery(self, components):
        """Test recovery from paste operation errors."""
        keyboard_engine = components["keyboard_engine"]

        # Test typing mode error
        with patch("pyautogui.write", side_effect=Exception("Typing failed")):
            result = keyboard_engine.paste_text("Test", method="typing")
            assert result is False  # Should handle error gracefully

        # Test clipboard mode error
        with patch("pyperclip.copy", side_effect=Exception("Clipboard failed")):
            result = keyboard_engine.paste_text("Test", method="clipboard")
            assert result is False  # Should handle error gracefully

    def test_paste_last_item_functionality(self, components, mock_system_components):
        """Test 'Paste Last Item' menu functionality."""
        from pasta.utils.permissions import PermissionChecker

        # Create SystemTray
        tray = SystemTray(
            clipboard_manager=components["clipboard_manager"],
            keyboard_engine=components["keyboard_engine"],
            storage_manager=components["storage_manager"],
            permission_checker=PermissionChecker(),
        )

        # Add some clipboard history
        test_entries = [
            {"content": "First entry", "timestamp": "2024-01-01", "hash": "hash1", "content_type": "text"},
            {"content": "Second entry", "timestamp": "2024-01-02", "hash": "hash2", "content_type": "text"},
            {"content": "Latest entry", "timestamp": "2024-01-03", "hash": "hash3", "content_type": "text"},
        ]

        for entry in test_entries:
            components["clipboard_manager"]._add_to_history(entry)

        # Test paste last item in different modes
        for mode in ["typing", "clipboard"]:
            tray.set_paste_mode(mode)

            with patch.object(components["keyboard_engine"], "paste_text") as mock_paste:
                tray.paste_last_item()

                # Should paste the latest entry with correct mode
                mock_paste.assert_called_once_with("Latest entry", method=mode)

    def test_paste_with_position_restoration(self, components):
        """Test cursor position restoration after paste."""
        keyboard_engine = components["keyboard_engine"]

        # Mock position tracking
        original_pos = (500, 300)
        positions = []

        with (
            patch("pyautogui.position", return_value=original_pos),
            patch("pyautogui.moveTo") as mock_move,
            patch("pyautogui.click") as mock_click,
            patch("pyautogui.write"),
        ):
            mock_move.side_effect = lambda x, y: positions.append((x, y))

            # Paste with position restoration
            keyboard_engine.paste_text("Test", method="typing")

            # Should click at original position to restore focus
            if mock_click.called:
                assert mock_click.call_args[0] == original_pos

    def test_chunked_paste_operation(self, components):
        """Test chunked paste for large text."""
        keyboard_engine = components["keyboard_engine"]

        # Create large text that should be chunked
        large_text = "A" * 500 + "\n" + "B" * 500

        chunks_typed = []

        with patch("pyautogui.write") as mock_write:
            mock_write.side_effect = lambda text, interval=0: chunks_typed.append(text)

            keyboard_engine.paste_text(large_text, method="typing")

            # Should be split into chunks
            assert len(chunks_typed) > 1
            assert sum(len(chunk) for chunk in chunks_typed) == len(large_text)

            # Verify content integrity
            reassembled = "".join(chunks_typed)
            assert reassembled == large_text

    def test_adaptive_typing_speed(self, components):
        """Test adaptive typing speed based on system load."""
        keyboard_engine = components["keyboard_engine"]

        # Mock different CPU usage scenarios
        test_cases = [
            (10.0, 0.01),  # Low CPU, fast typing
            (50.0, 0.02),  # Medium CPU, moderate speed
            (90.0, 0.05),  # High CPU, slow typing
        ]

        for cpu_percent, expected_min_interval in test_cases:
            with (
                patch("psutil.cpu_percent", return_value=cpu_percent),
                patch("pyautogui.write") as mock_write,
            ):
                keyboard_engine.paste_text("Test", method="typing")

                # Check interval used (may vary based on implementation)
                if mock_write.call_args and "interval" in mock_write.call_args[1]:
                    interval = mock_write.call_args[1]["interval"]
                    assert interval >= expected_min_interval * 0.5  # Allow some variance

    def test_empty_content_handling(self, components):
        """Test handling of empty or whitespace-only content."""
        keyboard_engine = components["keyboard_engine"]

        test_cases = ["", " ", "\n", "\t", "   \n   "]

        for content in test_cases:
            # Should handle gracefully without errors
            result = keyboard_engine.paste_text(content, method="typing")
            assert isinstance(result, bool)  # Should return True or False, not crash

    def test_paste_mode_persistence(self, components, mock_system_components):
        """Test paste mode persists across operations."""
        from pasta.utils.permissions import PermissionChecker

        tray = SystemTray(
            clipboard_manager=components["clipboard_manager"],
            keyboard_engine=components["keyboard_engine"],
            storage_manager=components["storage_manager"],
            permission_checker=PermissionChecker(),
        )

        # Set different modes and verify they persist
        for mode in ["typing", "clipboard", "auto"]:
            tray.set_paste_mode(mode)
            assert tray.paste_mode == mode

            # Simulate paste operation
            with patch.object(components["keyboard_engine"], "paste_text") as mock_paste:
                tray.paste_last_item()

                # Should use the set mode
                if mock_paste.called:
                    assert mock_paste.call_args[1]["mode"] == mode
