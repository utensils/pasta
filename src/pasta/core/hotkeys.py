"""Global hotkey management for Pasta."""

import contextlib
import threading
from typing import Callable, Optional

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except Exception:
    # Keyboard module not available or failed to initialize
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
                # Register double ESC for emergency stop
                keyboard.add_hotkey(self.abort_hotkey, self._on_abort_hotkey, suppress=False)
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
                keyboard.remove_hotkey(self.abort_hotkey)
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
