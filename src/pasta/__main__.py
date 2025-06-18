"""Main entry point for Pasta application."""

import os
import sys
from pathlib import Path

from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.settings import SettingsManager
from pasta.core.storage import StorageManager
from pasta.gui.tray import SystemTray
from pasta.utils.permissions import PermissionChecker


def main() -> None:
    """Run the Pasta application."""
    print("Pasta - Clipboard to Keyboard Bridge")
    print("Starting application...")

    # Check permissions first
    permission_checker = PermissionChecker()
    if not permission_checker.check_permissions():
        print("\n⚠️  Pasta requires additional permissions to function properly.")
        print(permission_checker.get_permission_error_message())
        print("\nSetup instructions:")
        print(permission_checker.get_permission_instructions())

        # Try to request permissions
        permission_checker.request_permissions()

        # Exit for now (user needs to grant permissions and restart)
        print("\nPlease grant the required permissions and restart Pasta.")
        sys.exit(1)

    # Initialize components
    clipboard_manager = ClipboardManager()
    keyboard_engine = PastaKeyboardEngine()

    # Use default database location
    # Store in user's data directory
    if sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / "Pasta"
    elif sys.platform == "win32":
        data_dir = Path(os.getenv("APPDATA", "")) / "Pasta"
    else:
        data_dir = Path.home() / ".local" / "share" / "pasta"

    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(data_dir / "history.db")

    storage_manager = StorageManager(db_path)

    # Create settings manager
    settings_manager = SettingsManager()
    settings_manager.load()  # Load saved settings

    # Create system tray
    tray = SystemTray(
        clipboard_manager=clipboard_manager,
        keyboard_engine=keyboard_engine,
        storage_manager=storage_manager,
        permission_checker=permission_checker,
        settings_manager=settings_manager,
    )

    print("\n✅ Pasta is running in the system tray!")
    print("🍝 Copy text to clipboard and watch it being typed!")
    print("⚡ Emergency Stop: Double ESC or click tray icon during paste")
    print("🔧 Right-click the tray icon to access options")
    print("⌨️  Press Ctrl+C to quit\n")

    try:
        # Run the application
        tray.run()
    except KeyboardInterrupt:
        print("\nShutting down Pasta...")
        tray.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
