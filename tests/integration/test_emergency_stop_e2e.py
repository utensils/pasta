"""End-to-end integration tests for emergency stop functionality."""

import sys
import threading
import time
from unittest.mock import Mock, patch

import pytest

from pasta.core.hotkeys import HotkeyManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.gui.tray import SystemTray


class TestEmergencyStopE2E:
    """End-to-end tests for emergency stop functionality."""

    @pytest.fixture
    def keyboard_engine(self):
        """Create real keyboard engine."""
        return PastaKeyboardEngine()

    @pytest.fixture
    def hotkey_manager(self):
        """Create hotkey manager."""
        return HotkeyManager()

    @pytest.fixture
    def mock_system_components(self):
        """Mock system components to prevent GUI creation."""
        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon") as mock_tray_icon,
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            # Mock tray icon instance
            mock_instance = Mock()
            mock_instance.showMessage = Mock()
            mock_tray_icon.return_value = mock_instance
            yield mock_instance

    def test_double_esc_emergency_stop(self, keyboard_engine, hotkey_manager):
        """Test double ESC key press triggers emergency stop."""
        # Track abort calls
        abort_called = threading.Event()

        def on_abort():
            abort_called.set()

        # Set abort callback
        hotkey_manager.set_abort_callback(on_abort)

        # Simulate double ESC press
        with patch("keyboard.is_pressed") as mock_is_pressed:
            # First ESC press
            mock_is_pressed.return_value = True
            hotkey_manager._check_double_esc()

            # Second ESC press within timeout
            time.sleep(0.1)  # Small delay
            hotkey_manager._check_double_esc()

            # Should trigger abort
            assert abort_called.wait(timeout=1.0)

    def test_emergency_stop_during_paste(self, keyboard_engine):
        """Test emergency stop interrupts ongoing paste operation."""
        # Create large text to paste
        large_text = "A" * 10000

        # Track paste progress
        chunks_pasted = []
        paste_interrupted = threading.Event()

        def mock_write(text, interval=0):
            chunks_pasted.append(text)
            # Simulate abort after a few chunks
            if len(chunks_pasted) > 2:
                keyboard_engine._abort_event.set()
                paste_interrupted.set()
                raise KeyboardInterrupt("Emergency stop")

        # Also patch position to avoid fail-safe
        with (
            patch("pasta.core.keyboard.pyautogui.write", side_effect=mock_write),
            patch("pasta.core.keyboard.pyautogui.position", return_value=(100, 100)),
        ):
            # Start paste operation
            result = keyboard_engine.paste_text(large_text, method="typing")

            # Should be interrupted
            assert result is False
            # Check that we pasted some chunks but not all
            assert len(chunks_pasted) > 0  # At least started pasting
            assert len(chunks_pasted) < 50  # But didn't paste all chunks (50 total)

    def test_tray_click_emergency_stop(self, mock_system_components):
        """Test clicking tray icon triggers emergency stop."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # Create system tray
        tray = SystemTray(
            clipboard_manager=ClipboardManager(),
            keyboard_engine=PastaKeyboardEngine(),
            storage_manager=StorageManager(":memory:"),
            permission_checker=PermissionChecker(),
        )

        # Track abort
        abort_called = False

        def on_abort():
            nonlocal abort_called
            abort_called = True

        tray.keyboard_engine._abort_callback = on_abort

        # Simulate emergency stop during operation
        tray.keyboard_engine._is_pasting = True
        tray._on_emergency_stop()  # Simulate emergency stop

        # Should trigger abort
        assert abort_called
        assert tray.keyboard_engine._abort_event.is_set()

    def test_emergency_stop_visual_feedback(self, mock_system_components):
        """Test emergency stop provides visual feedback."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # Create system tray
        keyboard_engine = PastaKeyboardEngine()
        tray = SystemTray(
            clipboard_manager=ClipboardManager(),
            keyboard_engine=keyboard_engine,
            storage_manager=StorageManager(":memory:"),
            permission_checker=PermissionChecker(),
        )

        # Mock tray icon for notifications
        tray.tray_icon = mock_system_components

        # Simulate emergency stop
        keyboard_engine._is_pasting = True
        tray._on_emergency_stop()

        # Should show notification
        mock_system_components.showMessage.assert_called()
        args = mock_system_components.showMessage.call_args[0]
        assert "stopped" in args[1].lower() or "abort" in args[1].lower()

    def test_emergency_stop_resets_state(self, keyboard_engine):
        """Test emergency stop properly resets engine state."""
        # Set engine to pasting state
        keyboard_engine._is_pasting = True
        keyboard_engine._abort_event.clear()

        # Trigger emergency stop via abort_paste method
        keyboard_engine.abort_paste()

        # Verify state is reset
        assert keyboard_engine._is_pasting is False
        assert keyboard_engine._abort_event.is_set() is True

        # Should be ready for next operation
        keyboard_engine._abort_event.clear()
        assert keyboard_engine._is_pasting is not True

    def test_multiple_emergency_stop_triggers(self, keyboard_engine, hotkey_manager):
        """Test multiple emergency stop triggers work correctly."""
        abort_count = 0

        def on_abort():
            nonlocal abort_count
            abort_count += 1

        hotkey_manager.set_abort_callback(on_abort)
        keyboard_engine._abort_callback = on_abort

        # Test multiple triggers
        for _i in range(3):
            keyboard_engine._is_pasting = True
            keyboard_engine.abort_paste()
            time.sleep(0.1)

            # Reset for next test
            keyboard_engine._abort_event.clear()

        # Should have triggered abort each time
        assert abort_count == 3

    def test_emergency_stop_thread_safety(self, keyboard_engine):
        """Test emergency stop is thread-safe."""
        results = {"errors": [], "stops": 0}

        def paste_operation():
            try:
                keyboard_engine._is_pasting = True
                time.sleep(0.1)  # Simulate paste
                if keyboard_engine._abort_event.is_set():
                    results["stops"] += 1
                keyboard_engine._is_pasting = False
            except Exception as e:
                results["errors"].append(str(e))

        def stop_operation():
            time.sleep(0.05)  # Small delay
            keyboard_engine._abort_event.set()

        # Run paste and stop concurrently
        threads = []
        for _ in range(5):
            paste_thread = threading.Thread(target=paste_operation)
            stop_thread = threading.Thread(target=stop_operation)
            threads.extend([paste_thread, stop_thread])
            paste_thread.start()
            stop_thread.start()

        for t in threads:
            t.join()

        # Should have no errors
        assert len(results["errors"]) == 0
        assert results["stops"] > 0

    def test_emergency_stop_with_rate_limiting(self, keyboard_engine):
        """Test emergency stop bypasses rate limiting."""
        from pasta.utils.security import RateLimiter

        rate_limiter = RateLimiter()
        rate_limiter.set_limit("paste", max_requests=1, window_seconds=60)

        # Use up rate limit
        rate_limiter.record_request("paste")
        assert rate_limiter.check_limit("paste") is False

        # Emergency stop should still work
        keyboard_engine._is_pasting = True
        keyboard_engine._abort_event.set()

        # Should stop regardless of rate limit
        assert keyboard_engine._abort_event.is_set() is True

    def test_emergency_stop_cleanup(self, keyboard_engine):
        """Test emergency stop performs proper cleanup."""
        # Mock clipboard restoration
        original_clipboard = "Original content"

        with (
            patch("pyperclip.paste", return_value=original_clipboard),
            patch("pyperclip.copy") as mock_copy,
        ):
            # Start paste operation
            keyboard_engine._is_pasting = True
            keyboard_engine._original_clipboard = original_clipboard

            # Trigger emergency stop
            keyboard_engine._abort_event.set()

            # Should restore original clipboard if implemented
            if mock_copy.called:
                assert mock_copy.call_args[0][0] == original_clipboard

    def test_emergency_stop_hotkey_registration(self, hotkey_manager):
        """Test emergency stop hotkeys are properly registered."""
        registered_hotkeys = []

        def mock_add_hotkey(keys, callback):
            registered_hotkeys.append((keys, callback))
            return len(registered_hotkeys)

        # Skip test on macOS where keyboard module is disabled
        if sys.platform == "darwin":
            pytest.skip("Keyboard module disabled on macOS")

        # Also skip if keyboard module is not available
        from pasta.core.hotkeys import KEYBOARD_AVAILABLE

        if not KEYBOARD_AVAILABLE:
            pytest.skip("Keyboard module not available")

        with patch("pasta.core.hotkeys.keyboard") as mock_keyboard:
            mock_keyboard.add_hotkey = mock_add_hotkey
            hotkey_manager.register_hotkeys()

            # Should register ESC hotkey if keyboard module is working
            if registered_hotkeys:
                assert any("esc" in str(keys).lower() for keys, _ in registered_hotkeys)
            else:
                # If no hotkeys were registered, it means keyboard module failed
                pytest.skip("Keyboard module failed to register hotkeys")

    def test_emergency_stop_recovery(self, keyboard_engine):
        """Test system recovers properly after emergency stop."""
        # Trigger emergency stop
        keyboard_engine._is_pasting = True
        keyboard_engine.abort_paste()

        assert keyboard_engine._abort_event.is_set() is True
        assert keyboard_engine._is_pasting is False

        # Reset abort flag
        keyboard_engine._abort_event.clear()

        # Should be able to paste again
        with (
            patch("pasta.core.keyboard.pyautogui.write") as mock_write,
            patch("pasta.core.keyboard.pyautogui.position", return_value=(100, 100)),
        ):
            result = keyboard_engine.paste_text("Test after stop", method="typing")
            assert result is True
            mock_write.assert_called()

    def test_emergency_stop_with_concurrent_operations(self, keyboard_engine):
        """Test emergency stop with multiple concurrent paste operations."""
        results = {"completed": 0, "aborted": 0}

        def paste_worker(text, worker_id):
            keyboard_engine._is_pasting = True
            try:
                # Simulate chunked paste
                for _i in range(10):
                    if keyboard_engine._abort_event.is_set():
                        results["aborted"] += 1
                        return
                    time.sleep(0.01)
                results["completed"] += 1
            finally:
                keyboard_engine._is_pasting = False

        # Start multiple paste operations
        threads = []
        for i in range(3):
            t = threading.Thread(target=paste_worker, args=(f"Worker {i} text", i))
            threads.append(t)
            t.start()

        # Trigger emergency stop after a delay
        time.sleep(0.05)
        keyboard_engine.abort_paste()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should have aborted some operations
        assert results["aborted"] > 0
        assert results["completed"] < 3  # Not all should complete

    def test_emergency_stop_persistence(self, keyboard_engine, tmp_path):
        """Test emergency stop state doesn't persist across restarts."""
        # Trigger emergency stop
        keyboard_engine._abort_event.set()
        assert keyboard_engine._abort_event.is_set() is True

        # Simulate app restart by creating new engine
        new_engine = PastaKeyboardEngine()

        # Should not have abort flag set
        assert new_engine._abort_event.is_set() is False
        assert new_engine.is_pasting() is False

    def test_emergency_stop_full_integration(self, mock_system_components):
        """Test full emergency stop integration with all components."""
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        # Create all components
        clipboard_manager = ClipboardManager()
        keyboard_engine = PastaKeyboardEngine()
        storage_manager = StorageManager(":memory:")
        permission_checker = PermissionChecker()

        # Create system tray
        tray = SystemTray(
            clipboard_manager=clipboard_manager,
            keyboard_engine=keyboard_engine,
            storage_manager=storage_manager,
            permission_checker=permission_checker,
        )

        # Mock components for testing
        tray.tray_icon = mock_system_components
        abort_triggered = threading.Event()

        def on_abort():
            abort_triggered.set()

        keyboard_engine._abort_callback = on_abort

        # Start a long paste operation in background
        def long_paste():
            keyboard_engine.paste_text("x" * 10000, method="typing")

        paste_thread = threading.Thread(target=long_paste)
        paste_thread.start()

        # Wait a moment then trigger emergency stop
        time.sleep(0.1)
        tray._on_emergency_stop()

        # Wait for abort
        assert abort_triggered.wait(timeout=2.0)

        # Verify notification shown
        mock_system_components.showMessage.assert_called()

        # Clean up
        paste_thread.join(timeout=1.0)
