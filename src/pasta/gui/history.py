"""History window for viewing clipboard history."""

from PyQt6.QtWidgets import QMainWindow

from pasta.core.storage import StorageManager


class HistoryWindow(QMainWindow):
    """Window for viewing clipboard history."""

    def __init__(self, storage_manager: StorageManager) -> None:
        """Initialize the history window.

        Args:
            storage_manager: StorageManager instance
        """
        super().__init__()
        self.storage_manager = storage_manager
        self.setWindowTitle("Pasta - History")
        self.resize(600, 400)
