"""System tray interface for Pasta - redirects to PySide6 implementation."""

# Import the PySide6 implementation
from pasta.gui.tray_pyside6 import SystemTray  # noqa: F401

__all__ = ["SystemTray"]
