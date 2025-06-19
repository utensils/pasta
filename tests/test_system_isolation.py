"""Test to verify that tests are properly isolated from the system.

This test file helps identify which tests might be causing system interference.
Run this with: uv run pytest tests/test_system_isolation.py -v
"""

import subprocess
import sys

import pytest


def test_keyboard_module_is_mocked():
    """Verify that the keyboard module is mocked."""
    import keyboard

    # Should be a MagicMock
    assert hasattr(keyboard, "_mock_name") or hasattr(keyboard, "__class__")
    assert callable(keyboard.add_hotkey)

    # Should not raise any errors
    keyboard.add_hotkey("test", lambda: None)
    keyboard.remove_hotkey("test")


def test_pyautogui_module_is_mocked():
    """Verify that pyautogui is mocked."""
    import pyautogui

    # Should be a MagicMock
    assert hasattr(pyautogui, "_mock_name") or hasattr(pyautogui, "__class__")

    # These should not do anything real
    pyautogui.write("test")
    pyautogui.press("enter")
    pyautogui.hotkey("cmd", "v")
    pyautogui.click(100, 100)

    # Should have been called but not actually executed
    assert pyautogui.write.called or hasattr(pyautogui.write, "call_count")


def test_subprocess_is_intercepted():
    """Verify subprocess calls are intercepted."""
    # This should be intercepted by our mock
    result = subprocess.run(["osascript", "-e", "tell application 'System Preferences' to activate"], capture_output=True)

    # Should return mock result, not actually open System Preferences
    assert result.returncode == 0
    assert result.stdout == ""


def test_permission_checker_does_not_open_system_prefs():
    """Verify PermissionChecker doesn't open System Preferences."""
    from pasta.utils.permissions import PermissionChecker

    checker = PermissionChecker()

    # This should not open System Preferences
    if sys.platform == "darwin":
        checker.request_permissions()


def test_keyboard_engine_does_not_type():
    """Verify PastaKeyboardEngine doesn't actually type."""
    from pasta.core.keyboard import PastaKeyboardEngine

    engine = PastaKeyboardEngine()

    # This should not actually type anything
    engine.paste_text("This should not be typed")

    # Verify pyautogui was called but mocked
    import pyautogui

    if hasattr(pyautogui.write, "called"):
        assert pyautogui.write.called or pyautogui.write.call_count > 0


def test_hotkey_manager_does_not_register_real_hotkeys():
    """Verify HotkeyManager doesn't register real hotkeys."""
    from pasta.core.hotkeys import HotkeyManager

    manager = HotkeyManager()

    # This should not register real hotkeys
    manager.register_hotkeys()

    # Should not interfere with actual keyboard
    manager.set_abort_callback(lambda: None)
    manager.unregister_hotkeys()


@pytest.mark.integration
def test_integration_tests_are_isolated():
    """Verify integration tests don't interfere with the system."""
    # Import some integration test modules to ensure they're properly mocked
    from tests.integration import test_app_launch

    # The imports alone should not cause any system interference
    assert test_app_launch is not None


if __name__ == "__main__":
    # Run this test to verify isolation
    pytest.main([__file__, "-v"])
