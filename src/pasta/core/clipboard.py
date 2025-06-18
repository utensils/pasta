"""Clipboard monitoring and management module."""

import hashlib
import threading
import time
from datetime import datetime
from typing import Any, Callable, Optional

import pyperclip


class ClipboardManager:
    """Manages clipboard monitoring and history.

    This class provides clipboard monitoring functionality with history
    tracking and change detection.

    Attributes:
        history: List of clipboard entries
        history_size: Maximum number of entries to keep
        monitoring: Whether monitoring is active
    """

    def __init__(self, history_size: int = 100) -> None:
        """Initialize the ClipboardManager.

        Args:
            history_size: Maximum number of clipboard entries to store
        """
        self.history: list[dict[str, Any]] = []
        self.history_size = history_size
        self.monitoring = False
        self.callbacks: list[Callable] = []
        self._last_hash = ""
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()  # Thread safety

    def start_monitoring(self) -> None:
        """Start monitoring clipboard for changes."""
        if self.monitoring:
            return

        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop monitoring clipboard."""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring:
            try:  # noqa: SIM105
                self._monitor_iteration()
            except Exception:
                # Silently handle errors to keep monitoring alive
                pass
            time.sleep(0.5)

    def _monitor_iteration(self) -> None:
        """Single iteration of monitoring."""
        try:
            content = pyperclip.paste()

            # Skip empty or whitespace-only content
            if not content or not content.strip():
                return

            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Skip if content hasn't changed
            if content_hash == self._last_hash:
                return

            self._last_hash = content_hash

            # Create entry
            entry = {
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "hash": content_hash,
                "content_type": self._detect_content_type(content),
            }

            # Add to history
            self._add_to_history(entry)

            # Notify callbacks
            for callback in self.callbacks:
                try:  # noqa: SIM105
                    callback(entry)
                except Exception:
                    # Don't let callback errors stop monitoring
                    pass

        except Exception:
            # Handle clipboard access errors
            pass

    def _detect_content_type(self, content: str) -> str:
        """Detect type of clipboard content.

        Args:
            content: Content to analyze

        Returns:
            Content type string
        """
        if content.startswith(("http://", "https://")):
            return "url"
        elif "\t" in content or "\n" in content:
            return "multiline"
        elif len(content) > 500:
            return "large_text"
        else:
            return "text"

    def _add_to_history(self, entry: dict[str, Any]) -> None:
        """Add entry to history with deduplication.

        Args:
            entry: Entry to add
        """
        with self._lock:
            # Remove duplicates
            self.history = [e for e in self.history if e["hash"] != entry["hash"]]

            # Add new entry at beginning
            self.history.insert(0, entry)

            # Trim history to size limit
            if len(self.history) > self.history_size:
                self.history = self.history[: self.history_size]

    def register_callback(self, callback: Callable) -> None:
        """Register callback for clipboard changes.

        Args:
            callback: Function to call on clipboard changes
        """
        self.callbacks.append(callback)

    def get_history(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Get clipboard history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of clipboard entries
        """
        with self._lock:
            if limit is None:
                return self.history.copy()
            return self.history[:limit].copy()

    def clear_history(self) -> None:
        """Clear all clipboard history."""
        with self._lock:
            self.history.clear()
            self._last_hash = ""
