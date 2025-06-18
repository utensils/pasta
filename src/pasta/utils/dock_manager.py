"""macOS dock icon visibility management."""

import sys
import threading
from typing import Optional


class DockIconManager:
    """Manages macOS dock icon visibility based on window state.

    This singleton class controls whether the application icon appears in the
    macOS dock. When no windows are open, the app runs as a background process
    (LSUIElement). When windows are open, it shows in the dock for better UX.

    Attributes:
        _instance: Singleton instance
        _references: Set of window references currently open
        _visible: Whether dock icon is currently visible
        _lock: Thread lock for thread safety
    """

    _instance: Optional["DockIconManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DockIconManager":
        """Create or return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the dock icon manager."""
        # Only initialize once
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._references: set[str] = set()
        self._visible = False
        self._ref_lock = threading.Lock()

        # Only functional on macOS
        self._is_macos = sys.platform == "darwin"
        self._appkit_available = False

        if self._is_macos:
            try:
                # Import at module level to avoid issues
                global AppKit
                import AppKit

                self._appkit_available = True
            except ImportError:
                # AppKit not available (e.g., in some test environments)
                self._appkit_available = False

    @classmethod
    def get_instance(cls) -> "DockIconManager":
        """Get the singleton instance."""
        return cls()

    def add_reference(self, window_id: str) -> None:
        """Add a window reference and show dock icon if needed.

        Args:
            window_id: Unique identifier for the window (e.g., "settings", "history")
        """
        if not self._is_macos or not self._appkit_available:
            return

        with self._ref_lock:
            self._references.add(window_id)
            if not self._visible:
                self.show()

    def remove_reference(self, window_id: str) -> None:
        """Remove a window reference and hide dock icon if no windows remain.

        Args:
            window_id: Unique identifier for the window
        """
        if not self._is_macos or not self._appkit_available:
            return

        with self._ref_lock:
            self._references.discard(window_id)
            if not self._references and self._visible:
                self.hide()

    def show(self) -> None:
        """Show the application icon in the dock."""
        if not self._is_macos or not self._appkit_available:
            return

        try:
            # Use the global AppKit that was imported
            import sys

            appkit_module = sys.modules.get("AppKit")
            if not appkit_module:
                return

            # Get the main bundle's info dictionary
            info = appkit_module.NSBundle.mainBundle().infoDictionary()
            # Set LSUIElement to False (0) to show in dock
            info["LSUIElement"] = "0"
            self._visible = True

            # Transform to regular app
            appkit_module.NSApp.setActivationPolicy_(appkit_module.NSApplicationActivationPolicyRegular)
        except Exception:
            # Fail silently - dock icon is nice to have but not critical
            pass

    def hide(self) -> None:
        """Hide the application icon from the dock."""
        if not self._is_macos or not self._appkit_available:
            return

        try:
            # Use the global AppKit that was imported
            import sys

            appkit_module = sys.modules.get("AppKit")
            if not appkit_module:
                return

            # Get the main bundle's info dictionary
            info = appkit_module.NSBundle.mainBundle().infoDictionary()
            # Set LSUIElement to True (1) to hide from dock
            info["LSUIElement"] = "1"
            self._visible = False

            # Transform to accessory app (no dock icon)
            appkit_module.NSApp.setActivationPolicy_(appkit_module.NSApplicationActivationPolicyAccessory)
        except Exception:
            # Fail silently
            pass

    def is_visible(self) -> bool:
        """Check if dock icon is currently visible.

        Returns:
            True if dock icon is visible, False otherwise
        """
        return self._visible

    def reset(self) -> None:
        """Reset the manager state (mainly for testing)."""
        with self._ref_lock:
            self._references.clear()
            if self._visible:
                self.hide()

    @classmethod
    def _reset_singleton(cls) -> None:
        """Reset singleton instance (for testing only)."""
        cls._instance = None
