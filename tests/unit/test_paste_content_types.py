"""Test paste_last_item with different content types."""

from unittest.mock import Mock, patch

import pytest

from pasta.gui.tray_pyside6 import SystemTray


class TestPasteContentTypes:
    """Test paste_last_item with different content types."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "clipboard_manager": Mock(),
            "keyboard_engine": Mock(),
            "storage_manager": Mock(),
            "permission_checker": Mock(),
            "settings_manager": Mock(),
        }

    @pytest.fixture
    def tray(self, mock_components):
        """Create a SystemTray instance for testing."""
        # Mock the settings
        mock_components["settings_manager"].settings.monitoring_enabled = True
        mock_components["settings_manager"].settings.paste_mode = "auto"
        mock_components["settings_manager"].settings.emergency_stop_hotkey = "Escape+Escape"

        with (
            patch("pasta.gui.tray_pyside6.QApplication"),
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
            patch("pasta.gui.tray_pyside6.QPixmap"),
            patch("pasta.gui.tray_pyside6.QPainter"),
        ):
            tray = SystemTray(**mock_components)
            tray._update_menu = Mock()
            tray._update_tray_icon = Mock()
            return tray

    def test_paste_text_type(self, tray, mock_components):
        """Test pasting content with 'text' type."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        test_entry = {"content": "Simple text content", "content_type": "text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        tray.paste_last_item()

        mock_components["keyboard_engine"].paste_text.assert_called_once_with("Simple text content", method="typing")

    def test_paste_multiline_type(self, tray, mock_components):
        """Test pasting content with 'multiline' type."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        multiline_content = """First line
Second line
Third line"""

        test_entry = {"content": multiline_content, "content_type": "multiline", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        tray.paste_last_item()

        # Should paste multiline content
        mock_components["keyboard_engine"].paste_text.assert_called_once_with(multiline_content, method="typing")

    def test_paste_large_text_type(self, tray, mock_components):
        """Test pasting content with 'large_text' type."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        large_content = "x" * 600

        test_entry = {"content": large_content, "content_type": "large_text", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        tray.paste_last_item()

        # Should paste large text content
        mock_components["keyboard_engine"].paste_text.assert_called_once_with(large_content, method="typing")

    def test_paste_url_type(self, tray, mock_components):
        """Test pasting content with 'url' type."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        url_content = "https://example.com/page"

        test_entry = {"content": url_content, "content_type": "url", "timestamp": "2024-01-01T12:00:00", "hash": "test_hash"}
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        tray.paste_last_item()

        # Should NOT paste URL type (not in allowed types)
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_paste_mixed_content_with_tabs(self, tray, mock_components):
        """Test pasting content with tabs (classified as multiline)."""
        tray.enabled = True
        tray.set_paste_mode("typing")

        tab_content = "Column1\tColumn2\tColumn3"

        test_entry = {
            "content": tab_content,
            "content_type": "multiline",  # Tab content is classified as multiline
            "timestamp": "2024-01-01T12:00:00",
            "hash": "test_hash",
        }
        mock_components["storage_manager"].get_entries.return_value = [test_entry]

        tray.paste_last_item()

        # Should paste tab content
        mock_components["keyboard_engine"].paste_text.assert_called_once_with(tab_content, method="typing")
