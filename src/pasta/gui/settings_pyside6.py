"""Settings window using PySide6."""

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pasta.core.settings import SettingsManager


class SettingsWindow(QDialog):
    """Settings window for configuring Pasta."""

    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None) -> None:
        """Initialize the settings window.

        Args:
            settings_manager: SettingsManager instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings.copy()  # Work with a copy

        self.setWindowTitle("Pasta Settings")
        self.setGeometry(100, 100, 600, 500)
        self.setModal(False)  # Non-modal dialog

        # macOS-specific: Ensure window appears in dock and handles Cmd+Q properly
        if sys.platform == "darwin":
            # Window should appear in dock when open
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

            # Add Cmd+Q shortcut that only closes this window
            cmd_q = QShortcut(QKeySequence("Ctrl+Q"), self)  # Ctrl+Q is Cmd+Q on macOS
            cmd_q.activated.connect(self.close)

        # Create layout
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self._create_general_tab()
        self._create_performance_tab()
        self._create_history_tab()
        self._create_privacy_tab()
        self._create_hotkeys_tab()

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def _create_general_tab(self) -> None:
        """Create the General settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout()

        self.start_on_login = QCheckBox("Start Pasta on system login")
        self.start_on_login.setChecked(self.settings.start_on_login)
        startup_layout.addRow(self.start_on_login)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        # Monitoring group
        monitoring_group = QGroupBox("Monitoring")
        monitoring_layout = QFormLayout()

        self.monitoring_enabled = QCheckBox("Enable clipboard monitoring")
        self.monitoring_enabled.setChecked(self.settings.monitoring_enabled)
        monitoring_layout.addRow(self.monitoring_enabled)

        self.paste_mode = QComboBox()
        self.paste_mode.addItems(["auto", "clipboard", "typing"])
        self.paste_mode.setCurrentText(self.settings.paste_mode)
        monitoring_layout.addRow("Default paste mode:", self.paste_mode)

        monitoring_group.setLayout(monitoring_layout)
        layout.addWidget(monitoring_group)

        layout.addStretch()
        self.tabs.addTab(tab, "General")

    def _create_performance_tab(self) -> None:
        """Create the Performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Typing speed group
        speed_group = QGroupBox("Typing Speed")
        speed_layout = QFormLayout()

        self.typing_speed = QSlider(Qt.Orientation.Horizontal)
        self.typing_speed.setRange(10, 500)
        self.typing_speed.setValue(self.settings.typing_speed)
        self.typing_speed.setTickInterval(50)
        self.typing_speed.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.speed_label = QLabel(f"{self.settings.typing_speed} chars/sec")
        self.typing_speed.valueChanged.connect(lambda v: self.speed_label.setText(f"{v} chars/sec"))

        speed_layout.addRow("Typing speed:", self.typing_speed)
        speed_layout.addRow("", self.speed_label)

        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(50, 1000)
        self.chunk_size.setValue(self.settings.chunk_size)
        self.chunk_size.setSingleStep(50)
        speed_layout.addRow("Chunk size:", self.chunk_size)

        self.adaptive_delay = QCheckBox("Use adaptive delays based on system load")
        self.adaptive_delay.setChecked(self.settings.adaptive_delay)
        speed_layout.addRow(self.adaptive_delay)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        layout.addStretch()
        self.tabs.addTab(tab, "Performance")

    def _create_history_tab(self) -> None:
        """Create the History settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # History settings group
        history_group = QGroupBox("History Settings")
        history_layout = QFormLayout()

        self.history_size = QSpinBox()
        self.history_size.setRange(10, 10000)
        self.history_size.setValue(self.settings.history_size)
        self.history_size.setSingleStep(10)
        history_layout.addRow("Maximum entries:", self.history_size)

        self.history_retention = QSpinBox()
        self.history_retention.setRange(1, 365)
        self.history_retention.setValue(self.settings.history_retention_days)
        self.history_retention.setSuffix(" days")
        history_layout.addRow("Keep history for:", self.history_retention)

        self.encrypt_sensitive = QCheckBox("Encrypt sensitive clipboard data")
        self.encrypt_sensitive.setChecked(self.settings.encrypt_sensitive)
        history_layout.addRow(self.encrypt_sensitive)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        self.tabs.addTab(tab, "History")

    def _create_privacy_tab(self) -> None:
        """Create the Privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Privacy mode
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QFormLayout()

        self.privacy_mode = QCheckBox("Enable privacy mode")
        self.privacy_mode.setChecked(self.settings.privacy_mode)
        privacy_layout.addRow(self.privacy_mode)

        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)

        # Excluded apps
        excluded_group = QGroupBox("Excluded Applications")
        excluded_layout = QVBoxLayout()

        excluded_label = QLabel("Clipboard monitoring will be disabled for these applications:")
        excluded_layout.addWidget(excluded_label)

        self.excluded_apps_list = QListWidget()
        self.excluded_apps_list.addItems(self.settings.excluded_apps)
        excluded_layout.addWidget(self.excluded_apps_list)

        # Add/Remove buttons
        button_layout = QHBoxLayout()
        self.add_app_button = QPushButton("Add...")
        self.add_app_button.clicked.connect(self.add_excluded_app)
        button_layout.addWidget(self.add_app_button)

        self.remove_app_button = QPushButton("Remove")
        self.remove_app_button.clicked.connect(self.remove_excluded_app)
        button_layout.addWidget(self.remove_app_button)

        excluded_layout.addLayout(button_layout)
        excluded_group.setLayout(excluded_layout)
        layout.addWidget(excluded_group)

        # Excluded patterns
        patterns_group = QGroupBox("Excluded Patterns")
        patterns_layout = QVBoxLayout()

        patterns_label = QLabel("Text matching these patterns will not be stored:")
        patterns_layout.addWidget(patterns_label)

        self.excluded_patterns = QTextEdit()
        self.excluded_patterns.setPlainText("\n".join(self.settings.excluded_patterns))
        self.excluded_patterns.setMaximumHeight(100)
        patterns_layout.addWidget(self.excluded_patterns)

        patterns_group.setLayout(patterns_layout)
        layout.addWidget(patterns_group)

        self.tabs.addTab(tab, "Privacy")

    def _create_hotkeys_tab(self) -> None:
        """Create the Hotkeys settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Hotkeys group
        hotkeys_group = QGroupBox("Global Hotkeys")
        hotkeys_layout = QFormLayout()

        self.emergency_stop_hotkey = QLineEdit()
        self.emergency_stop_hotkey.setText(self.settings.emergency_stop_hotkey)
        self.emergency_stop_hotkey.setPlaceholderText("e.g., esc+esc")
        hotkeys_layout.addRow("Emergency stop:", self.emergency_stop_hotkey)

        self.quick_paste_hotkey = QLineEdit()
        self.quick_paste_hotkey.setText(self.settings.quick_paste_hotkey)
        self.quick_paste_hotkey.setPlaceholderText("e.g., ctrl+shift+v")
        hotkeys_layout.addRow("Quick paste:", self.quick_paste_hotkey)

        self.toggle_monitoring_hotkey = QLineEdit()
        self.toggle_monitoring_hotkey.setText(self.settings.toggle_monitoring_hotkey)
        self.toggle_monitoring_hotkey.setPlaceholderText("e.g., ctrl+shift+m")
        hotkeys_layout.addRow("Toggle monitoring:", self.toggle_monitoring_hotkey)

        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        # Note
        note_label = QLabel("Note: Hotkey functionality may be limited on macOS due to system restrictions.")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        layout.addStretch()
        self.tabs.addTab(tab, "Hotkeys")

    def add_excluded_app(self) -> None:
        """Add an application to the excluded list."""
        from PySide6.QtWidgets import QInputDialog

        app_name, ok = QInputDialog.getText(self, "Add Excluded Application", "Enter application name:")
        if ok and app_name:
            self.excluded_apps_list.addItem(app_name)

    def remove_excluded_app(self) -> None:
        """Remove selected application from excluded list."""
        current_item = self.excluded_apps_list.currentItem()
        if current_item:
            self.excluded_apps_list.takeItem(self.excluded_apps_list.row(current_item))

    def apply_settings(self) -> None:
        """Apply settings without closing dialog."""
        # Update settings from UI
        self.settings.start_on_login = self.start_on_login.isChecked()
        self.settings.monitoring_enabled = self.monitoring_enabled.isChecked()
        self.settings.paste_mode = self.paste_mode.currentText()
        self.settings.typing_speed = self.typing_speed.value()
        self.settings.chunk_size = self.chunk_size.value()
        self.settings.adaptive_delay = self.adaptive_delay.isChecked()
        self.settings.history_size = self.history_size.value()
        self.settings.history_retention_days = self.history_retention.value()
        self.settings.encrypt_sensitive = self.encrypt_sensitive.isChecked()
        self.settings.privacy_mode = self.privacy_mode.isChecked()

        # Excluded apps
        excluded_apps = []
        for i in range(self.excluded_apps_list.count()):
            item = self.excluded_apps_list.item(i)
            if item is not None:
                excluded_apps.append(item.text())
        self.settings.excluded_apps = excluded_apps

        # Excluded patterns
        patterns_text = self.excluded_patterns.toPlainText()
        self.settings.excluded_patterns = [p.strip() for p in patterns_text.split("\n") if p.strip()]

        # Hotkeys
        self.settings.emergency_stop_hotkey = self.emergency_stop_hotkey.text()
        self.settings.quick_paste_hotkey = self.quick_paste_hotkey.text()
        self.settings.toggle_monitoring_hotkey = self.toggle_monitoring_hotkey.text()

        # Save settings
        self.settings_manager.update_settings(self.settings)
        self.settings_manager.save()

        QMessageBox.information(self, "Settings", "Settings applied successfully.")

    def accept_settings(self) -> None:
        """Apply settings and close dialog."""
        self.apply_settings()
        self.accept()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle window close event.

        On macOS, this ensures Cmd+Q only closes the window, not the app.

        Args:
            event: The close event
        """
        # Accept the close event (close only this window)
        event.accept()
