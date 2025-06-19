"""Global hotkey management for Pasta."""

import contextlib
import sys
import threading
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    import keyboard as keyboard_typing
else:
    keyboard_typing = None

# The keyboard module has issues on macOS that can cause CoreFoundation crashes
# Disable it on macOS until we implement a proper solution using pynput or other alternatives
if sys.platform == "darwin":
    keyboard = None
    KEYBOARD_AVAILABLE = False
else:
    try:
        import keyboard

        KEYBOARD_AVAILABLE = True
    except Exception:
        # Keyboard module not available or failed to initialize
        keyboard = None
        KEYBOARD_AVAILABLE = False


class HotkeyManager:
    """Manages global hotkeys for the application.

    This class handles registration and management of global hotkeys,
    particularly the emergency stop functionality.

    Attributes:
        abort_callback: Function to call when abort hotkey is pressed
        abort_hotkey: The hotkey combination for emergency stop
    """

    def __init__(self) -> None:
        """Initialize the HotkeyManager."""
        self.abort_callback: Optional[Callable[[], None]] = None
        self.abort_hotkey = "esc+esc"  # Double ESC for emergency stop
        self._registered = False
        self._lock = threading.Lock()
        self._last_esc_time = 0.0
        self._double_esc_timeout = 0.5  # 500ms timeout for double ESC

    def set_abort_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for emergency abort.

        Args:
            callback: Function to call when abort hotkey is pressed
        """
        with self._lock:
            self.abort_callback = callback

    def register_hotkeys(self) -> None:
        """Register all global hotkeys."""
        with self._lock:
            if self._registered:
                return

            if not KEYBOARD_AVAILABLE:
                # Keyboard module not available
                return

            try:
                # Register ESC hotkey for double-press detection
                keyboard.add_hotkey("esc", self._check_double_esc, suppress=False)  # type: ignore[attr-defined]
                self._registered = True
            except Exception:
                # Hotkey registration failed
                pass

    def unregister_hotkeys(self) -> None:
        """Unregister all global hotkeys."""
        with self._lock:
            if not self._registered:
                return

            if not KEYBOARD_AVAILABLE:
                # Keyboard module not available
                self._registered = False
                return

            try:
                keyboard.remove_hotkey(self.abort_hotkey)  # type: ignore[attr-defined]
                self._registered = False
            except Exception:
                # Even if removal fails, mark as unregistered
                self._registered = False

    def _on_abort_hotkey(self) -> None:
        """Handle abort hotkey press."""
        if self.abort_callback:
            with contextlib.suppress(Exception):
                # Don't let callback errors crash hotkey handling
                self.abort_callback()

    def _check_double_esc(self) -> None:
        """Check for double ESC press pattern."""
        import time

        current_time = time.time()

        if current_time - self._last_esc_time < self._double_esc_timeout:
            # Double ESC detected
            if self.abort_callback:
                with contextlib.suppress(Exception):
                    self.abort_callback()
            self._last_esc_time = 0  # Reset to prevent triple-ESC
        else:
            # First ESC press
            self._last_esc_time = current_time
