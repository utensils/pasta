"""Main entry point for Pasta application."""
import sys
from typing import NoReturn


def main() -> NoReturn:
    """Run the Pasta application.

    This is the main entry point that initializes and starts
    the system tray application.
    """
    print("Pasta - Clipboard to Keyboard Bridge")
    print("Starting application...")

    # TODO: Initialize clipboard manager
    # TODO: Initialize keyboard engine
    # TODO: Initialize system tray
    # TODO: Start main event loop

    print("Application started. Running in system tray...")

    # Placeholder - will be replaced with actual implementation
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down Pasta...")
        sys.exit(0)


if __name__ == "__main__":
    main()
