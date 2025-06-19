"""System tray interface for Pasta using PySide6."""

import contextlib
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Optional, cast

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from pasta.core.clipboard import ClipboardManager
from pasta.core.hotkeys import HotkeyManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.settings import Settings, SettingsManager
from pasta.core.storage import StorageManager

# We'll import these inline when needed to avoid circular imports
from pasta.utils.permissions import PermissionChecker


class ClipboardWorker(QObject):
    """Worker thread for clipboard monitoring."""

    clipboard_changed = Signal(dict)

    def __init__(self, clipboard_manager: ClipboardManager) -> None:
        """Initialize the worker."""
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.clipboard_manager.register_callback(self._on_clipboard_change)

    def _on_clipboard_change(self, entry: dict[str, Any]) -> None:
        """Handle clipboard change in worker thread."""
        self.clipboard_changed.emit(entry)


class SystemTray(QObject):
    """System tray interface for Pasta using PySide6.

    This class manages the system tray icon and menu,
    coordinating between all core components.

    Attributes:
        clipboard_manager: ClipboardManager instance
        keyboard_engine: PastaKeyboardEngine instance
        storage_manager: StorageManager instance
        permission_checker: PermissionChecker instance
        enabled: Whether paste functionality is enabled
    """

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        keyboard_engine: PastaKeyboardEngine,
        storage_manager: StorageManager,
        permission_checker: PermissionChecker,
        settings_manager: Optional[SettingsManager] = None,
    ) -> None:
        """Initialize the SystemTray.

        Args:
            clipboard_manager: ClipboardManager instance
            keyboard_engine: PastaKeyboardEngine instance
            storage_manager: StorageManager instance
            permission_checker: PermissionChecker instance
            settings_manager: SettingsManager instance (optional)
        """
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.keyboard_engine = keyboard_engine
        self.storage_manager = storage_manager
        self.permission_checker = permission_checker
        self.settings_manager = settings_manager or SettingsManager()

        # State - use settings
        self.enabled = self.settings_manager.settings.monitoring_enabled
        self.paste_mode = self.settings_manager.settings.paste_mode
        self._lock = threading.Lock()

        # Qt application
        self._app: Optional[QApplication] = None
        self._init_qt_app()

        # Hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.set_abort_callback(self._on_emergency_stop)

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self._setup_tray_icon()

        # Create clipboard worker thread
        self._clipboard_thread = QThread()
        self._clipboard_worker = ClipboardWorker(self.clipboard_manager)
        self._clipboard_worker.moveToThread(self._clipboard_thread)
        self._clipboard_worker.clipboard_changed.connect(self._on_clipboard_change)

        # Register as settings observer
        self.settings_manager.add_observer(self._on_settings_changed)

        # References to windows
        self._history_window: Optional[Any] = None  # Will be PySide6HistoryWindow
        self._settings_window: Optional[Any] = None  # Will be PySide6SettingsWindow

    def _init_qt_app(self) -> None:
        """Initialize Qt application if needed."""
        if QApplication.instance() is None:
            self._app = QApplication(sys.argv)
            # Set application name so dialogs show "Pasta" instead of "python"
            self._app.setApplicationName("Pasta")
            self._app.setApplicationDisplayName("Pasta")
            # Set organization for QSettings
            self._app.setOrganizationName("Utensils")
            self._app.setOrganizationDomain("utensils.dev")
            # Don't quit when last window is closed (we're a tray app)
            self._app.setQuitOnLastWindowClosed(False)

            # macOS-specific configuration
            if sys.platform == "darwin":
                try:
                    # Try to set the app to run as accessory (no dock icon)
                    # This only works when running as a proper app bundle
                    import AppKit  # type: ignore[import-untyped]

                    AppKit.NSApplication.sharedApplication().setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
                except ImportError:
                    # PyObjC not available, will rely on Info.plist LSUIElement
                    pass
        else:
            self._app = cast(Optional[QApplication], QApplication.instance())

    def _setup_tray_icon(self) -> None:
        """Set up the system tray icon."""
        # Store base icon path
        self.base_icon_path = Path(__file__).parent / "resources" / "pasta.png"

        # Update icon based on current mode
        self._update_tray_icon()

        # Create menu
        self._create_menu()

        # Connect signals
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Show the tray icon
        self.tray_icon.show()

    def _update_tray_icon(self) -> None:
        """Update the tray icon based on current mode and state."""
        if not self.base_icon_path.exists():
            self.tray_icon.setIcon(QIcon())
            return

        # Load base icon
        pixmap = QPixmap(str(self.base_icon_path))

        # Modify icon based on mode
        if self.paste_mode == "typing":
            # Tint icon orange for typing mode
            painted_pixmap = QPixmap(pixmap.size())
            painted_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(painted_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawPixmap(0, 0, pixmap)

            # Apply orange tint
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            painter.fillRect(painted_pixmap.rect(), Qt.GlobalColor.darkYellow)
            painter.end()

            pixmap = painted_pixmap
            tooltip = "Pasta - Typing Mode Active"
        elif self.paste_mode == "clipboard":
            # Tint icon blue for clipboard mode
            painted_pixmap = QPixmap(pixmap.size())
            painted_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(painted_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawPixmap(0, 0, pixmap)

            # Apply blue tint
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            painter.fillRect(painted_pixmap.rect(), Qt.GlobalColor.darkCyan)
            painter.end()

            pixmap = painted_pixmap
            tooltip = "Pasta - Clipboard Mode Active"
        else:
            # Default auto mode
            tooltip = "Pasta - Clipboard History Manager"

        # Apply disabled state if needed
        if not self.enabled:
            # Make icon semi-transparent for disabled state
            painted_pixmap = QPixmap(pixmap.size())
            painted_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(painted_pixmap)
            painter.setOpacity(0.5)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            pixmap = painted_pixmap
            tooltip += " (Disabled)"

        # Set the icon and tooltip
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip(tooltip)

    def _create_menu(self) -> None:
        """Create the tray menu."""
        menu = QMenu()

        # Paste Mode submenu
        paste_mode_menu = menu.addMenu(f"Paste Mode: {self.paste_mode.capitalize()}")

        auto_action = QAction("Auto", self)
        auto_action.setCheckable(True)
        auto_action.setChecked(self.paste_mode == "auto")
        auto_action.triggered.connect(lambda: self.set_paste_mode("auto"))
        paste_mode_menu.addAction(auto_action)

        clipboard_action = QAction("Clipboard", self)
        clipboard_action.setCheckable(True)
        clipboard_action.setChecked(self.paste_mode == "clipboard")
        clipboard_action.triggered.connect(lambda: self.set_paste_mode("clipboard"))
        paste_mode_menu.addAction(clipboard_action)

        typing_action = QAction("Typing", self)
        typing_action.setCheckable(True)
        typing_action.setChecked(self.paste_mode == "typing")
        typing_action.triggered.connect(lambda: self.set_paste_mode("typing"))
        paste_mode_menu.addAction(typing_action)

        menu.addSeparator()

        # Paste last item
        paste_action = QAction(f"Paste Last Item ({self.paste_mode})", self)
        paste_action.setEnabled(self.enabled)
        paste_action.triggered.connect(lambda: QTimer.singleShot(100, self.paste_last_item))
        menu.addAction(paste_action)

        # Enabled toggle
        enabled_action = QAction("Enabled", self)
        enabled_action.setCheckable(True)
        enabled_action.setChecked(self.enabled)
        enabled_action.triggered.connect(self.toggle_enabled)
        menu.addAction(enabled_action)

        # Emergency stop
        emergency_action = QAction("Emergency Stop (Double ESC)", self)
        emergency_action.setEnabled(self.keyboard_engine.is_pasting())
        emergency_action.triggered.connect(self._on_emergency_stop)
        menu.addAction(emergency_action)

        menu.addSeparator()

        # History
        history_action = QAction("History", self)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)

        # Settings
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        # About
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)

        # Quit
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation.

        Args:
            reason: The activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - emergency stop if pasting
            if self.keyboard_engine.is_pasting():
                self._on_emergency_stop()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # Right-click is handled by context menu
            pass

    def _on_clipboard_change(self, entry: dict[str, Any]) -> None:
        """Handle clipboard content change.

        Args:
            entry: Clipboard entry dict with content, timestamp, etc.
        """
        # Always save to history, regardless of enabled state
        with contextlib.suppress(Exception):
            # Save to storage
            self.storage_manager.save_entry(entry)

        # Note: Typing/clipboard modes now only affect how paste operations work,
        # not whether they happen automatically. Use the history window or
        # manual paste operations to trigger paste with the selected method.

    def paste_last_item(self) -> None:
        """Paste the last clipboard item using the current paste mode."""
        if not self.enabled:
            return

        # Get the most recent entry from history
        entries = self.storage_manager.get_entries(limit=1)
        if not entries:
            return

        entry = entries[0]
        content_type = entry.get("content_type")
        if content_type in ("text", "multiline", "large_text") and entry.get("content"):
            # Note: The menu action is already deferred by QTimer.singleShot
            # which allows the menu to close and focus to return properly
            try:
                # Determine paste method based on mode
                if self.paste_mode == "typing":
                    self.keyboard_engine.paste_text(entry["content"], method="typing")
                elif self.paste_mode == "clipboard":
                    self.keyboard_engine.paste_text(entry["content"], method="clipboard")
                else:
                    # Auto mode - use clipboard by default
                    self.keyboard_engine.paste_text(entry["content"], method="clipboard")
            except Exception:
                # Silently handle exceptions to avoid disrupting user experience
                pass

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

        # Update menu
        self._update_menu()

    def set_paste_mode(self, mode: str) -> None:
        """Set the paste mode.

        Args:
            mode: Paste mode ('auto', 'clipboard', or 'typing')
        """
        with self._lock:
            self.paste_mode = mode
        self._update_tray_icon()
        self._update_menu()

    def _update_menu(self) -> None:
        """Update the tray menu to reflect current state."""
        # Update icon to reflect current state
        self._update_tray_icon()
        # Recreate menu to update checkmarks and labels
        self._create_menu()

    def show_history(self) -> None:
        """Show the history window."""
        # Create and show history window
        from pasta.gui.history_pyside6 import HistoryWindow as PySide6HistoryWindow

        window = PySide6HistoryWindow(self.storage_manager)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.show()

        # Keep reference to prevent garbage collection
        self._history_window = window

    def show_settings(self) -> None:
        """Show the settings window."""
        # Create and show settings window
        from pasta.gui.settings_pyside6 import SettingsWindow as PySide6SettingsWindow

        window = PySide6SettingsWindow(settings_manager=self.settings_manager)
        window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        window.show()

        # Keep reference to prevent garbage collection
        self._settings_window = window

    def show_about(self) -> None:
        """Show about information."""
        # Open project URL
        webbrowser.open("https://github.com/utensils/pasta")

    def quit(self) -> None:
        """Quit the application."""
        # Stop monitoring
        self.clipboard_manager.stop_monitoring()

        # Stop clipboard thread
        if self._clipboard_thread.isRunning():
            self._clipboard_thread.quit()
            self._clipboard_thread.wait()

        # Unregister hotkeys
        self.hotkey_manager.unregister_hotkeys()

        # Hide tray icon
        self.tray_icon.hide()

        # Quit app
        if self._app:
            self._app.quit()

    def run(self) -> None:
        """Run the system tray application."""
        # Start clipboard monitoring in thread
        self._clipboard_thread.start()

        # Start monitoring if enabled
        if self.enabled:
            self.clipboard_manager.start_monitoring()

        # Register hotkeys
        self.hotkey_manager.register_hotkeys()

        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system.")
            return

        # Run the application
        if self._app:
            sys.exit(self._app.exec())

    def _on_emergency_stop(self) -> None:
        """Handle emergency stop request."""
        # Abort any ongoing paste
        self.keyboard_engine.abort_paste()

        # Update menu to reflect state
        self._update_menu()

        # Flash the icon or show notification
        print("⚠️  Emergency stop activated! Paste operation aborted.")
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Pasta",
                "Emergency stop activated! Paste operation aborted.",
                QSystemTrayIcon.MessageIcon.Warning,
                2000,  # Show for 2 seconds
            )

    def _on_settings_changed(self, settings: Settings) -> None:
        """Handle settings changes.

        Args:
            settings: Updated Settings instance
        """
        # Update state from settings
        self.enabled = settings.monitoring_enabled
        self.paste_mode = settings.paste_mode

        # Update hotkeys
        self.hotkey_manager.abort_hotkey = settings.emergency_stop_hotkey

        # Update menu
        self._update_menu()
