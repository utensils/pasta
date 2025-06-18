"""System tray interface for Pasta."""

import contextlib
import threading
import webbrowser
from pathlib import Path
from typing import Any, Optional

import pystray
from PIL import Image
from PyQt6.QtWidgets import QApplication
from pystray import Menu, MenuItem

from pasta.core.clipboard import ClipboardManager
from pasta.core.hotkeys import HotkeyManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.gui.history import HistoryWindow
from pasta.gui.settings import SettingsWindow
from pasta.utils.permissions import PermissionChecker


class SystemTray:
    """System tray interface for Pasta.

    This class manages the system tray icon and menu,
    coordinating between all core components.

    Attributes:
        clipboard_manager: ClipboardManager instance
        keyboard_engine: PastaKeyboardEngine instance
        storage_manager: StorageManager instance
        permission_checker: PermissionChecker instance
        icon: pystray Icon instance
        enabled: Whether paste functionality is enabled
    """

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        keyboard_engine: PastaKeyboardEngine,
        storage_manager: StorageManager,
        permission_checker: PermissionChecker,
    ) -> None:
        """Initialize the SystemTray.

        Args:
            clipboard_manager: ClipboardManager instance
            keyboard_engine: PastaKeyboardEngine instance
            storage_manager: StorageManager instance
            permission_checker: PermissionChecker instance
        """
        self.clipboard_manager = clipboard_manager
        self.keyboard_engine = keyboard_engine
        self.storage_manager = storage_manager
        self.permission_checker = permission_checker

        # State
        self.enabled = True
        self.paste_mode = "auto"
        self._lock = threading.Lock()

        # Qt application for windows
        self._qt_app: Optional[QApplication] = None

        # Hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_abort_callback(self._on_emergency_stop)

        # Set up clipboard callback
        self.clipboard_manager.register_callback(self._on_clipboard_change)

        # Create tray icon
        self.icon = self._create_icon()

        # Set up icon click handler
        self.icon.on_clicked = self._on_icon_clicked

    def _create_icon(self) -> pystray.Icon:
        """Create the system tray icon.

        Returns:
            pystray Icon instance
        """
        # Load icon image
        icon_path = Path(__file__).parent / "resources" / "pasta.png"
        image = Image.open(icon_path) if icon_path.exists() else self._create_default_icon()

        # Create menu
        menu = Menu(self._create_menu)

        # Create icon
        icon = pystray.Icon("Pasta", icon=image, menu=menu, title="Pasta - Clipboard to Keyboard")

        return icon

    def _create_default_icon(self) -> Image.Image:
        """Create a default icon if resource is missing.

        Returns:
            PIL Image
        """
        # Create a simple 64x64 icon
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        # Add a simple shape (will be replaced with actual icon)
        from PIL import ImageDraw

        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=(100, 150, 200, 255))
        draw.text((22, 20), "P", fill=(255, 255, 255, 255))
        return image

    def _create_menu(self) -> list[MenuItem]:
        """Create the tray menu.

        Returns:
            List of menu items
        """
        return [
            MenuItem(
                f"Paste Mode: {self.paste_mode.capitalize()}",
                Menu(
                    MenuItem("Auto", lambda: self.set_paste_mode("auto"), checked=lambda _: self.paste_mode == "auto"),
                    MenuItem("Clipboard", lambda: self.set_paste_mode("clipboard"), checked=lambda _: self.paste_mode == "clipboard"),
                    MenuItem("Typing", lambda: self.set_paste_mode("typing"), checked=lambda _: self.paste_mode == "typing"),
                ),
            ),
            Menu.SEPARATOR,
            MenuItem("Enabled", self.toggle_enabled, checked=lambda _: self.enabled),
            MenuItem("Emergency Stop (Double ESC)", self._on_emergency_stop, enabled=lambda _: self.keyboard_engine.is_pasting()),
            Menu.SEPARATOR,
            MenuItem("History", self.show_history),
            MenuItem("Settings", self.show_settings),
            Menu.SEPARATOR,
            MenuItem("About", self.show_about),
            MenuItem("Quit", self.quit),
        ]

    def _on_clipboard_change(self, entry: dict[str, Any]) -> None:
        """Handle clipboard content change.

        Args:
            entry: Clipboard entry dict with content, timestamp, etc.
        """
        if not self.enabled:
            return

        with contextlib.suppress(Exception):
            # Paste using current mode
            self.keyboard_engine.paste_text(entry["content"], method=self.paste_mode)

    def toggle_enabled(self) -> None:
        """Toggle paste functionality on/off."""
        with self._lock:
            if self.enabled:
                # Disable
                self.enabled = False
                self.clipboard_manager.stop_monitoring()
            else:
                # Check permissions before enabling
                if self.permission_checker.check_permissions():
                    self.enabled = True
                    self.clipboard_manager.start_monitoring()
                else:
                    # Permissions denied
                    self.permission_checker.request_permissions()

        # Update icon to reflect state
        self._update_icon()

    def set_paste_mode(self, mode: str) -> None:
        """Set the paste mode.

        Args:
            mode: Paste mode ('auto', 'clipboard', or 'typing')
        """
        with self._lock:
            self.paste_mode = mode
        self._update_icon()

    def _update_icon(self) -> None:
        """Update the tray icon to reflect current state."""
        # Update menu to reflect new state
        self.icon.update_menu()

    def show_history(self) -> None:
        """Show the history window."""
        # Ensure Qt app exists
        if not QApplication.instance():
            self._qt_app = QApplication([])

        # Create and show history window
        window = HistoryWindow(self.storage_manager)
        window.show()

        # Keep reference to prevent garbage collection
        self._history_window = window

    def show_settings(self) -> None:
        """Show the settings window."""
        # Ensure Qt app exists
        if not QApplication.instance():
            self._qt_app = QApplication([])

        # Create and show settings window
        window = SettingsWindow()
        window.show()

        # Keep reference to prevent garbage collection
        self._settings_window = window

    def show_about(self) -> None:
        """Show about information."""
        # Open project URL
        webbrowser.open("https://github.com/yourusername/pasta")

    def quit(self) -> None:
        """Quit the application."""
        # Stop monitoring
        self.clipboard_manager.stop_monitoring()

        # Unregister hotkeys
        self.hotkey_manager.unregister_hotkeys()

        # Stop icon
        self.icon.stop()

    def run(self) -> None:
        """Run the system tray application."""
        # Start clipboard monitoring
        self.clipboard_manager.start_monitoring()

        # Register hotkeys
        self.hotkey_manager.register_hotkeys()

        # Run the icon (blocks until quit)
        self.icon.run()

    def _on_emergency_stop(self) -> None:
        """Handle emergency stop request."""
        # Abort any ongoing paste
        self.keyboard_engine.abort_paste()

        # Update menu to reflect state
        self._update_icon()

        # Flash the icon or show notification
        print("⚠️  Emergency stop activated! Paste operation aborted.")

    def _on_icon_clicked(self, icon: pystray.Icon, item: Any) -> None:  # noqa: ARG002
        """Handle tray icon click.

        Args:
            icon: The icon that was clicked
            item: The menu item (None for direct click)
        """
        # If pasting, emergency stop
        if self.keyboard_engine.is_pasting():
            self._on_emergency_stop()
