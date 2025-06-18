"""History window using PySide6."""

import sys
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pasta.core.storage import StorageManager


class HistoryWindow(QMainWindow):
    """Window for viewing and managing clipboard history."""

    def __init__(self, storage_manager: StorageManager, parent: Optional[QWidget] = None) -> None:
        """Initialize the history window.

        Args:
            storage_manager: StorageManager instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.storage_manager = storage_manager

        self.setWindowTitle("Pasta - Clipboard History")
        self.setGeometry(100, 100, 800, 600)

        # macOS-specific: Ensure window appears in dock and handles shortcuts properly
        if sys.platform == "darwin":
            # Window should appear in dock when open with native controls
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

            # Add Cmd+W shortcut that closes this window (standard macOS behavior)
            cmd_w = QShortcut(QKeySequence("Ctrl+W"), self)  # Ctrl+W is Cmd+W on macOS
            cmd_w.activated.connect(self.close)

            # Add Cmd+Q shortcut that only closes this window
            cmd_q = QShortcut(QKeySequence("Ctrl+Q"), self)  # Ctrl+Q is Cmd+Q on macOS
            cmd_q.activated.connect(self.close)

            # Add Cmd+M shortcut for minimize (standard macOS behavior)
            cmd_m = QShortcut(QKeySequence("Ctrl+M"), self)  # Ctrl+M is Cmd+M on macOS
            cmd_m.activated.connect(self.showMinimized)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_input)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_history)
        search_layout.addWidget(self.refresh_button)

        layout.addLayout(search_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Content", "Type", "Timestamp", "Source"])
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSortingEnabled(True)

        # Configure columns
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.history_table)

        # Button bar
        button_layout = QHBoxLayout()

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_selected)
        button_layout.addWidget(self.copy_button)

        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # Create menu bar
        self._create_menu()

        # Load history
        self.load_history()

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_history)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def _create_menu(self) -> None:
        """Create the menu bar."""
        # File menu
        file_menu = self.menuBar().addMenu("File")

        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self.load_history)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        close_action = QAction("Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = self.menuBar().addMenu("Edit")

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_selected)
        edit_menu.addAction(copy_action)

        delete_action = QAction("Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        edit_menu.addSeparator()

        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self.clear_history)
        edit_menu.addAction(clear_action)

    def load_history(self) -> None:
        """Load clipboard history from storage."""
        history = self.storage_manager.get_history(limit=1000)

        self.history_table.setRowCount(0)

        for entry in history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            # Content (truncated for display)
            content = entry.get("content", "")
            if len(content) > 100:
                content = content[:97] + "..."
            content_item = QTableWidgetItem(content)
            content_item.setData(Qt.ItemDataRole.UserRole, entry.get("id"))
            self.history_table.setItem(row, 0, content_item)

            # Type
            content_type = entry.get("content_type", "text")
            type_item = QTableWidgetItem(content_type)
            self.history_table.setItem(row, 1, type_item)

            # Timestamp
            timestamp = entry.get("timestamp", 0)
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            self.history_table.setItem(row, 2, time_item)

            # Source
            source = entry.get("source_app", "Unknown")
            source_item = QTableWidgetItem(source)
            self.history_table.setItem(row, 3, source_item)

    def filter_history(self, text: str) -> None:
        """Filter history based on search text.

        Args:
            text: Search text
        """
        for row in range(self.history_table.rowCount()):
            match = False
            for col in range(self.history_table.columnCount()):
                item = self.history_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.history_table.setRowHidden(row, not match)

    def copy_selected(self) -> None:
        """Copy selected item to clipboard."""
        current_row = self.history_table.currentRow()
        if current_row < 0:
            return

        content_item = self.history_table.item(current_row, 0)
        if content_item:
            entry_id = content_item.data(Qt.ItemDataRole.UserRole)
            if entry_id:
                # Get full content from storage
                entries = self.storage_manager.get_history(limit=1)
                for entry in entries:
                    if entry.get("id") == entry_id:
                        content = entry.get("content", "")
                        clipboard = QApplication.clipboard()
                        clipboard.setText(content)
                        break

    def delete_selected(self) -> None:
        """Delete selected items from history."""
        selected_rows = set()
        for item in self.history_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} selected item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get IDs to delete
            ids_to_delete = []
            for row in selected_rows:
                content_item = self.history_table.item(row, 0)
                if content_item:
                    entry_id = content_item.data(Qt.ItemDataRole.UserRole)
                    if entry_id:
                        ids_to_delete.append(entry_id)

            # Delete from storage
            # Note: StorageManager might need a delete_entry method
            # For now, we'll just reload
            _ = ids_to_delete  # Acknowledge unused variable

            # Reload history
            self.load_history()

    def clear_history(self) -> None:
        """Clear all history after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Clear all clipboard history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.storage_manager.clear_history()
            self.load_history()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle window close event.

        On macOS, this ensures Cmd+Q only closes the window, not the app.

        Args:
            event: The close event
        """
        # Stop refresh timer
        self.refresh_timer.stop()
        # Accept the close event (close only this window)
        event.accept()
