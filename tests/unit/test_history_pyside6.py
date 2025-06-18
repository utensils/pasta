"""Tests for the PySide6 History window module."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from pasta.gui.history_pyside6 import HistoryWindow


class TestHistoryWindow:
    """Test cases for HistoryWindow."""

    @pytest.fixture
    def storage_manager(self):
        """Create a mock StorageManager."""
        manager = Mock()
        manager.get_history.return_value = [
            {
                "id": 1,
                "content": "Test content 1",
                "content_type": "text",
                "timestamp": 1234567890,
                "source_app": "TestApp",
            },
            {
                "id": 2,
                "content": "Test content 2 with a very long text that should be truncated in the display because it is longer than 100 characters",
                "content_type": "text",
                "timestamp": 1234567900,
                "source_app": "AnotherApp",
            },
        ]
        manager.clear_history.return_value = None
        return manager

    @pytest.fixture
    def window(self, storage_manager, qtbot):
        """Create a HistoryWindow for testing."""
        window = HistoryWindow(storage_manager)
        qtbot.addWidget(window)
        return window

    def test_initialization(self, window, storage_manager):
        """Test HistoryWindow initializes correctly."""
        assert window.storage_manager == storage_manager
        assert window.windowTitle() == "Pasta - Clipboard History"
        assert window.width() == 800
        assert window.height() == 600

    def test_history_table_setup(self, window):
        """Test history table is set up correctly."""
        assert window.history_table.columnCount() == 4
        headers = []
        for i in range(window.history_table.columnCount()):
            headers.append(window.history_table.horizontalHeaderItem(i).text())
        assert headers == ["Content", "Type", "Timestamp", "Source"]

    def test_load_history(self, window, storage_manager):
        """Test loading history from storage."""
        # History should be loaded on initialization
        assert window.history_table.rowCount() == 2

        # Check first row
        assert window.history_table.item(0, 0).text() == "Test content 1"
        assert window.history_table.item(0, 1).text() == "text"
        assert window.history_table.item(0, 3).text() == "TestApp"

        # Check content truncation
        content2 = window.history_table.item(1, 0).text()
        assert content2.endswith("...")
        assert len(content2) == 100

    def test_filter_history(self, window, qtbot):
        """Test filtering history entries."""
        # Set search text
        window.search_input.setText("content 1")

        # Check filtering
        assert not window.history_table.isRowHidden(0)
        assert window.history_table.isRowHidden(1)

        # Clear filter
        window.search_input.clear()
        assert not window.history_table.isRowHidden(0)
        assert not window.history_table.isRowHidden(1)

    def test_copy_selected(self, window, storage_manager, qtbot):
        """Test copying selected item to clipboard."""
        # Select first row
        window.history_table.selectRow(0)

        # Mock clipboard
        with patch("pasta.gui.history_pyside6.QApplication.clipboard") as mock_clipboard:
            clipboard_instance = Mock()
            mock_clipboard.return_value = clipboard_instance

            # Click copy button
            qtbot.mouseClick(window.copy_button, Qt.MouseButton.LeftButton)

            # Should copy the full content
            clipboard_instance.setText.assert_called_once_with("Test content 1")

    def test_copy_no_selection(self, window, qtbot):
        """Test copy when nothing is selected."""
        # Ensure nothing is selected
        window.history_table.clearSelection()

        with patch("pasta.gui.history_pyside6.QApplication.clipboard") as mock_clipboard:
            # Click copy button
            qtbot.mouseClick(window.copy_button, Qt.MouseButton.LeftButton)

            # Should not call clipboard
            mock_clipboard.assert_not_called()

    def test_delete_selected(self, window, storage_manager, qtbot):
        """Test deleting selected items."""
        # Select first row
        window.history_table.selectRow(0)

        # Mock confirmation dialog
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            # Click delete button
            qtbot.mouseClick(window.delete_button, Qt.MouseButton.LeftButton)

            # Should reload history
            assert storage_manager.get_history.call_count == 2  # Once on init, once on delete

    def test_delete_cancelled(self, window, storage_manager, qtbot):
        """Test cancelling delete operation."""
        # Select first row
        window.history_table.selectRow(0)

        # Mock confirmation dialog - user cancels
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            # Click delete button
            qtbot.mouseClick(window.delete_button, Qt.MouseButton.LeftButton)

            # Should not reload history
            assert storage_manager.get_history.call_count == 1  # Only on init

    def test_clear_history(self, window, storage_manager, qtbot):
        """Test clearing all history."""
        # Mock confirmation dialog
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            # Click clear button
            qtbot.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)

            # Should clear history in storage
            storage_manager.clear_history.assert_called_once()

            # Should reload history
            assert storage_manager.get_history.call_count == 2

    def test_clear_history_cancelled(self, window, storage_manager, qtbot):
        """Test cancelling clear history."""
        # Mock confirmation dialog - user cancels
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            # Click clear button
            qtbot.mouseClick(window.clear_button, Qt.MouseButton.LeftButton)

            # Should not clear history
            storage_manager.clear_history.assert_not_called()

    def test_refresh_button(self, window, storage_manager, qtbot):
        """Test refresh button reloads history."""
        # Click refresh button
        qtbot.mouseClick(window.refresh_button, Qt.MouseButton.LeftButton)

        # Should reload history
        assert storage_manager.get_history.call_count == 2  # Once on init, once on refresh

    def test_auto_refresh_timer(self, window, storage_manager, qtbot):
        """Test auto-refresh timer functionality."""
        # Timer should be active
        assert window.refresh_timer.isActive()
        assert window.refresh_timer.interval() == 5000

        # Trigger timer
        window.refresh_timer.timeout.emit()

        # Should reload history
        assert storage_manager.get_history.call_count == 2

    def test_close_window(self, window, qtbot):
        """Test closing the window."""
        # Timer should be active
        assert window.refresh_timer.isActive()

        # Close window
        window.close()

        # Timer should be stopped
        assert not window.refresh_timer.isActive()

    def test_menu_actions(self, window, storage_manager, qtbot):
        """Test menu bar actions."""
        # Test refresh action via menu
        refresh_action = None
        for action in window.menuBar().actions():
            if action.menu():
                for sub_action in action.menu().actions():
                    if sub_action.text() == "Refresh":
                        refresh_action = sub_action
                        break

        assert refresh_action is not None
        refresh_action.trigger()

        # Should reload history
        assert storage_manager.get_history.call_count == 2

    def test_timestamp_formatting(self, window):
        """Test timestamp is formatted correctly."""
        # Check timestamp formatting in table
        timestamp_item = window.history_table.item(0, 2)
        # Timestamp 1234567890 = 2009-02-13 23:31:30
        assert "2009" in timestamp_item.text()
        assert "02" in timestamp_item.text()
        assert "13" in timestamp_item.text()

    def test_case_insensitive_search(self, window):
        """Test search is case insensitive."""
        # Search with uppercase
        window.search_input.setText("CONTENT")

        # Both rows should be visible (both contain "content")
        assert not window.history_table.isRowHidden(0)
        assert not window.history_table.isRowHidden(1)

        # Search for specific app
        window.search_input.setText("testapp")
        assert not window.history_table.isRowHidden(0)
        assert window.history_table.isRowHidden(1)

    def test_empty_history(self, window, storage_manager, qtbot):
        """Test behavior with empty history."""
        # Set empty history
        storage_manager.get_history.return_value = []

        # Reload
        window.load_history()

        # Table should be empty
        assert window.history_table.rowCount() == 0

        # Operations should handle empty state gracefully
        qtbot.mouseClick(window.copy_button, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(window.delete_button, Qt.MouseButton.LeftButton)
