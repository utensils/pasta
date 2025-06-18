"""Settings window for configuring Pasta."""

from PyQt6.QtWidgets import QMainWindow


class SettingsWindow(QMainWindow):
    """Window for configuring Pasta settings."""

    def __init__(self) -> None:
        """Initialize the settings window."""
        super().__init__()
        self.setWindowTitle("Pasta - Settings")
        self.resize(500, 600)
