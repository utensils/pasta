"""Tests for the PySide6 SystemTray module."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QSystemTrayIcon

from pasta.gui.tray_pyside6 import ClipboardWorker, SystemTray


class TestSystemTray:
    """Test cases for PySide6 SystemTray."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            "clipboard_manager": Mock(),
            "keyboard_engine": Mock(),
            "storage_manager": Mock(),
            "permission_checker": Mock(),
        }

    @pytest.fixture
    def mock_qapp(self):
        """Mock QApplication for testing."""
        with patch("pasta.gui.tray_pyside6.QApplication") as mock_app:
            mock_instance = Mock()
            mock_app.instance.return_value = mock_instance
            yield mock_app

    @pytest.fixture
    def tray(self, mock_components, mock_qapp):
        """Create a SystemTray instance for testing."""
        # Create all the patches we need
        patches = [
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.Path"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            patch("pasta.gui.tray_pyside6.HotkeyManager"),
        ]

        with (
            patches[0] as mock_tray_icon,
            patches[1] as mock_qthread,
            patches[2],
            patches[3] as mock_qmenu,
            patches[4],
            patches[5] as mock_path,
            patches[6] as mock_worker,
            patches[7] as mock_hotkey_manager,
        ):
            # Mock icon path to not exist to avoid QPixmap creation
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value = mock_path_instance

            # Mock QThread to avoid moveToThread issues
            mock_thread_instance = Mock()
            mock_qthread.return_value = mock_thread_instance

            # Mock ClipboardWorker
            mock_worker_instance = Mock()
            mock_worker.return_value = mock_worker_instance

            # Mock QMenu to avoid widget creation
            mock_menu_instance = Mock()
            mock_qmenu.return_value = mock_menu_instance

            # Mock QSystemTrayIcon
            mock_tray_instance = Mock()
            mock_tray_icon.return_value = mock_tray_instance

            # Mock HotkeyManager
            mock_hotkey_instance = Mock()
            mock_hotkey_manager.return_value = mock_hotkey_instance

            tray = SystemTray(**mock_components)

            # Add the mocked instances to the tray for easier testing
            tray.tray_icon = mock_tray_instance
            tray._clipboard_thread = mock_thread_instance
            tray._clipboard_worker = mock_worker_instance
            tray.hotkey_manager = mock_hotkey_instance

            return tray

    def test_initialization(self, tray, mock_components):
        """Test SystemTray initializes correctly."""
        assert tray.clipboard_manager == mock_components["clipboard_manager"]
        assert tray.keyboard_engine == mock_components["keyboard_engine"]
        assert tray.storage_manager == mock_components["storage_manager"]
        assert tray.permission_checker == mock_components["permission_checker"]
        assert hasattr(tray, "tray_icon")
        assert hasattr(tray, "enabled")
        assert tray.enabled is True

    def test_qt_app_initialization(self, mock_components):
        """Test Qt application initialization."""
        with patch("pasta.gui.tray_pyside6.QApplication") as mock_qapp:
            # Test when no app exists
            mock_qapp.instance.return_value = None

            with (
                patch("pasta.gui.tray_pyside6.QSystemTrayIcon"),
                patch("pasta.gui.tray_pyside6.QThread"),
                patch("pasta.gui.tray_pyside6.QIcon"),
                patch("pasta.gui.tray_pyside6.QMenu"),
                patch("pasta.gui.tray_pyside6.QAction"),
                patch("pasta.gui.tray_pyside6.ClipboardWorker"),
            ):
                SystemTray(**mock_components)

            # Should create new QApplication
            mock_qapp.assert_called_once()
            # Should set app properties
            mock_qapp.return_value.setApplicationName.assert_called_with("Pasta")
            mock_qapp.return_value.setApplicationDisplayName.assert_called_with("Pasta")
            mock_qapp.return_value.setQuitOnLastWindowClosed.assert_called_with(False)

    @patch("pasta.gui.tray_pyside6.Path")
    def test_setup_tray_icon(self, mock_path, tray, mock_components, mock_qapp):
        """Test system tray icon setup."""
        # Create a fresh tray instance with proper mocking
        with (
            patch("pasta.gui.tray_pyside6.QSystemTrayIcon") as mock_tray_icon,
            patch("pasta.gui.tray_pyside6.QThread"),
            patch("pasta.gui.tray_pyside6.QIcon"),
            patch("pasta.gui.tray_pyside6.QMenu"),
            patch("pasta.gui.tray_pyside6.QAction"),
            patch("pasta.gui.tray_pyside6.ClipboardWorker"),
        ):
            # Mock icon file exists
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value = mock_path_instance

            mock_tray_instance = Mock()
            mock_tray_icon.return_value = mock_tray_instance

            _ = SystemTray(**mock_components)

            # Should set icon and tooltip
            mock_tray_instance.setIcon.assert_called()
            mock_tray_instance.setToolTip.assert_called_with("Pasta - Clipboard to Keyboard")
            mock_tray_instance.show.assert_called()

    def test_toggle_enabled(self, tray, mock_components):
        """Test toggling paste functionality."""
        # Start enabled
        assert tray.enabled is True

        # Mock _update_menu to avoid Qt widget creation
        with patch.object(tray, "_update_menu"):
            # Toggle off
            tray.toggle_enabled()
            assert tray.enabled is False
            mock_components["clipboard_manager"].stop_monitoring.assert_called()

            # Toggle on - permissions granted
            mock_components["permission_checker"].check_permissions.return_value = True
            tray.toggle_enabled()
            assert tray.enabled is True
            mock_components["clipboard_manager"].start_monitoring.assert_called()

    def test_toggle_enabled_no_permissions(self, tray, mock_components):
        """Test toggling when permissions denied."""
        tray.enabled = False
        mock_components["permission_checker"].check_permissions.return_value = False

        # Mock _update_menu to avoid Qt widget creation
        with patch.object(tray, "_update_menu"):
            tray.toggle_enabled()

            # Should remain disabled
            assert tray.enabled is False
            mock_components["permission_checker"].request_permissions.assert_called()

    def test_set_paste_mode(self, tray):
        """Test setting paste mode."""
        with patch.object(tray, "_update_menu") as mock_update:
            tray.set_paste_mode("typing")
            assert tray.paste_mode == "typing"
            mock_update.assert_called()

    def test_on_clipboard_change(self, tray, mock_components):
        """Test clipboard change handling."""
        entry = {"content": "test content", "timestamp": 123456}

        # When enabled
        tray.enabled = True
        tray._on_clipboard_change(entry)
        mock_components["keyboard_engine"].paste_text.assert_called_with("test content", method=tray.paste_mode)

        # When disabled
        tray.enabled = False
        mock_components["keyboard_engine"].reset_mock()
        tray._on_clipboard_change(entry)
        mock_components["keyboard_engine"].paste_text.assert_not_called()

    def test_on_emergency_stop(self, tray, mock_components):
        """Test emergency stop functionality."""
        with patch.object(tray, "_update_menu") as mock_update:
            tray._on_emergency_stop()

            mock_components["keyboard_engine"].abort_paste.assert_called()
            mock_update.assert_called()

    def test_show_history(self, tray):
        """Test showing history window."""
        with patch("pasta.gui.history_pyside6.HistoryWindow") as mock_window_class:
            mock_window = Mock()
            mock_window_class.return_value = mock_window

            tray.show_history()

            mock_window_class.assert_called_once()
            mock_window.setAttribute.assert_called()
            mock_window.show.assert_called()

    def test_show_settings(self, tray):
        """Test showing settings window."""
        with patch("pasta.gui.settings_pyside6.SettingsWindow") as mock_window_class:
            mock_window = Mock()
            mock_window_class.return_value = mock_window

            tray.show_settings()

            mock_window_class.assert_called_once()
            mock_window.setAttribute.assert_called()
            mock_window.show.assert_called()

    @patch("pasta.gui.tray_pyside6.webbrowser.open")
    def test_show_about(self, mock_webbrowser, tray):
        """Test showing about dialog."""
        tray.show_about()
        mock_webbrowser.assert_called_once_with("https://github.com/utensils/pasta")

    def test_quit(self, tray, mock_components):
        """Test quit functionality."""
        # Mock app
        tray._app = Mock()

        tray.quit()

        # Should stop monitoring
        mock_components["clipboard_manager"].stop_monitoring.assert_called()

        # Should stop thread
        tray._clipboard_thread.quit.assert_called()
        tray._clipboard_thread.wait.assert_called()

        # Should unregister hotkeys
        tray.hotkey_manager.unregister_hotkeys.assert_called()

        # Should hide tray icon
        tray.tray_icon.hide.assert_called()

        # Should quit app
        tray._app.quit.assert_called()

    def test_on_tray_activated_single_click(self, tray, mock_components):
        """Test tray icon single click during paste."""
        mock_components["keyboard_engine"].is_pasting.return_value = True

        with patch.object(tray, "_on_emergency_stop") as mock_stop:
            tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
            mock_stop.assert_called_once()

    def test_on_tray_activated_no_paste(self, tray, mock_components):
        """Test tray icon click when not pasting."""
        mock_components["keyboard_engine"].is_pasting.return_value = False

        with patch.object(tray, "_on_emergency_stop") as mock_stop:
            tray._on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
            mock_stop.assert_not_called()

    def test_settings_observer(self, tray):
        """Test settings change handling."""
        from pasta.core.settings import Settings

        new_settings = Settings(
            monitoring_enabled=False,
            paste_mode="clipboard",
            emergency_stop_hotkey="ctrl+q",
        )

        with patch.object(tray, "_update_menu") as mock_update:
            tray._on_settings_changed(new_settings)

            assert tray.enabled is False
            assert tray.paste_mode == "clipboard"
            assert tray.hotkey_manager.abort_hotkey == "ctrl+q"
            mock_update.assert_called()

    def test_run_method(self, tray, mock_components):
        """Test the run method."""
        # Mock QSystemTrayIcon.isSystemTrayAvailable
        with patch("pasta.gui.tray_pyside6.QSystemTrayIcon.isSystemTrayAvailable", return_value=True):
            # Mock app.exec() to prevent blocking
            tray._app = Mock()
            tray._app.exec.return_value = 0

            # Call run
            with pytest.raises(SystemExit) as exc_info:
                tray.run()

            assert exc_info.value.code == 0

            # Should start thread and monitoring
            tray._clipboard_thread.start.assert_called()
            mock_components["clipboard_manager"].start_monitoring.assert_called()

            # Should register hotkeys
            tray.hotkey_manager.register_hotkeys.assert_called()

            # Should run app
            tray._app.exec.assert_called()


class TestClipboardWorker:
    """Test cases for ClipboardWorker."""

    @pytest.fixture
    def worker(self):
        """Create a ClipboardWorker for testing."""
        clipboard_manager = Mock()
        return ClipboardWorker(clipboard_manager)

    def test_initialization(self, worker):
        """Test ClipboardWorker initialization."""
        assert hasattr(worker, "clipboard_manager")
        assert hasattr(worker, "clipboard_changed")
        worker.clipboard_manager.register_callback.assert_called_once()

    def test_clipboard_change_signal(self, worker):
        """Test clipboard change signal emission."""
        entry = {"content": "test", "timestamp": 123}

        # Connect a mock slot to the signal
        mock_slot = Mock()
        worker.clipboard_changed.connect(mock_slot)

        # Trigger clipboard change
        worker._on_clipboard_change(entry)

        # Should emit signal with entry
        mock_slot.assert_called_once_with(entry)
