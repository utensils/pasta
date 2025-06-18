"""Keyboard simulation and text input module."""

import platform
import threading
import time

import psutil
import pyautogui
import pyperclip


class AdaptiveTypingEngine:
    """Dynamically adjusts typing speed based on system performance."""

    def __init__(self) -> None:
        """Initialize the adaptive typing engine."""
        self.base_interval = 0.005
        self.max_interval = 0.05
        self.cpu_threshold = 70
        self.last_cpu_check = 0.0

    def get_typing_interval(self) -> float:
        """Calculate optimal typing interval based on system resources.

        Returns:
            Typing interval in seconds
        """
        current_time = time.time()

        # Check CPU every 2 seconds (or if never checked)
        if self.last_cpu_check == 0 or current_time - self.last_cpu_check > 2:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            self.last_cpu_check = current_time

            # Calculate stress factor (0-1)
            cpu_stress = cpu_percent / 100.0
            memory_stress = memory_info.percent / 100.0
            stress = (cpu_stress * 0.7) + (memory_stress * 0.3)

            # Scale interval based on stress
            interval = self.base_interval + (self.max_interval - self.base_interval) * stress
            return min(interval, self.max_interval)

        return self.base_interval


class PastaKeyboardEngine:
    """Handles keyboard simulation for pasting text.

    This class provides methods to simulate keyboard input,
    supporting both clipboard paste and character-by-character typing.

    Attributes:
        is_mac: Whether running on macOS
        paste_key: Platform-specific paste key modifier
    """

    def __init__(self, clipboard_threshold: int = 5000, chunk_size: int = 200) -> None:
        """Initialize the PastaKeyboardEngine.

        Args:
            clipboard_threshold: Text length threshold for choosing paste method
            chunk_size: Size of text chunks for typing method
        """
        # Platform detection
        self.is_mac = platform.system() == "Darwin"
        self.paste_key = "cmd" if self.is_mac else "ctrl"

        # Configuration
        self.clipboard_threshold = clipboard_threshold
        self.chunk_size = chunk_size

        # Optimize PyAutoGUI
        pyautogui.PAUSE = 0.01  # Reduce from default 0.1s
        pyautogui.FAILSAFE = True  # Safety feature

        # Adaptive typing engine
        self._adaptive_engine = AdaptiveTypingEngine()

        # Abort mechanism
        self._abort_event = threading.Event()
        self._is_pasting = False
        self._paste_lock = threading.Lock()

    def paste_text(self, text: str, method: str = "auto") -> bool:
        """Paste text using specified method.

        Args:
            text: Text to paste
            method: Paste method ('clipboard', 'typing', or 'auto')

        Returns:
            True if paste was successful, False otherwise
        """
        # Handle empty text
        if not text:
            return True

        # Reset abort event
        self._abort_event.clear()

        # Mark as pasting
        with self._paste_lock:
            self._is_pasting = True

        try:
            # Determine method
            if method == "auto":
                method = "clipboard" if len(text) < self.clipboard_threshold else "typing"
            elif method not in ("clipboard", "typing"):
                # Invalid method defaults to auto selection
                method = "clipboard" if len(text) < self.clipboard_threshold else "typing"

            if method == "clipboard":
                return self._paste_via_clipboard(text)
            else:
                return self._paste_via_typing(text)
        finally:
            with self._paste_lock:
                self._is_pasting = False

    def _paste_via_clipboard(self, text: str) -> bool:
        """Fast paste using system clipboard.

        Args:
            text: Text to paste

        Returns:
            Success status
        """
        try:
            # Store original clipboard content
            original = pyperclip.paste()

            # Copy new text to clipboard
            pyperclip.copy(text)

            # Perform paste
            pyautogui.hotkey(self.paste_key, "v")

            # Restore original clipboard content after delay
            time.sleep(0.1)
            pyperclip.copy(original)

            return True
        except Exception:
            return False

    def _paste_via_typing(self, text: str) -> bool:
        """Reliable character-by-character typing.

        Args:
            text: Text to type

        Returns:
            Success status
        """
        try:
            # Normalize line endings (handle \r\n and \r)
            text = text.replace("\r\n", "\n").replace("\r", "\n")

            # Handle multiline text
            lines = text.split("\n")

            # Small delay before starting to type (helps with focus issues)
            if len(lines) > 1:
                time.sleep(0.2)  # Increased delay for multi-line

            for i, line in enumerate(lines):
                # Type line in chunks
                for j in range(0, len(line), self.chunk_size):
                    # Check abort event
                    if self._abort_event.is_set():
                        return False

                    # Check fail-safe
                    if not self._check_continue():
                        return False

                    chunk = line[j : j + self.chunk_size]
                    pyautogui.write(chunk, interval=0.005)

                    # Pause between chunks
                    if j + self.chunk_size < len(line):
                        time.sleep(0.05)

                    # Check abort again after chunk
                    if self._abort_event.is_set():
                        return False

                # Add newline if not last line
                if i < len(lines) - 1:
                    # Small delay before pressing enter for multi-line
                    time.sleep(0.05)
                    pyautogui.press("enter")
                    # Small delay after enter to ensure it registers
                    time.sleep(0.05)

            return True
        except Exception:
            return False

    def _check_continue(self) -> bool:
        """Check if we should continue (fail-safe mechanism).

        Returns:
            True if safe to continue, False to abort
        """
        try:
            x, y = pyautogui.position()
            # Abort if mouse is in top-left corner (0, 0)
            return not (x == 0 and y == 0)
        except Exception:
            return True  # Continue on error

    def get_adaptive_engine(self) -> AdaptiveTypingEngine:
        """Get the adaptive typing engine instance.

        Returns:
            AdaptiveTypingEngine instance
        """
        return self._adaptive_engine

    def abort_paste(self) -> None:
        """Abort any ongoing paste operation immediately."""
        self._abort_event.set()

    def is_pasting(self) -> bool:
        """Check if currently pasting.

        Returns:
            True if paste operation is in progress
        """
        with self._paste_lock:
            return self._is_pasting
