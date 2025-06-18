"""Settings window for Pasta."""

from typing import Any, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pasta.core.settings import SettingsManager


class SettingsWindow(QMainWindow):
    """Settings window for configuring Pasta.

    This window provides a tabbed interface for configuring all
    aspects of the application.

    Attributes:
        settings_manager: SettingsManager instance
        original_settings: Copy of settings when window opened
    """

    settings_changed = pyqtSignal()

    def __init__(self, settings_manager: Optional[SettingsManager] = None) -> None:
        """Initialize the settings window.

        Args:
            settings_manager: SettingsManager instance (creates default if None)
        """
        super().__init__()
        self.settings_manager = settings_manager or SettingsManager()
        self.original_settings = self.settings_manager.settings.copy()

        self.setWindowTitle("Pasta - Settings")
        self.resize(600, 700)

        # Track unsaved changes
        self._has_changes = False

        # Set up UI
        self._setup_ui()
        self.load_settings()

        # Connect change tracking
        self._connect_change_tracking()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_performance_tab()
        self._create_history_tab()
        self._create_general_tab()
        self._create_privacy_tab()
        self._create_hotkeys_tab()

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Keyboard shortcuts
        self.save_button.setShortcut("Ctrl+S")
        self.cancel_button.setShortcut("Escape")

    def _create_performance_tab(self) -> None:
        """Create the performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Typing settings group
        typing_group = QGroupBox("Typing Settings")
        typing_layout = QFormLayout()

        # Typing speed
        self.typing_speed_spin = QSpinBox()
        self.typing_speed_spin.setRange(1, 1000)
        self.typing_speed_spin.setSuffix(" chars/sec")
        self.typing_speed_spin.setToolTip("How fast to type characters (1-1000 characters per second)")
        typing_layout.addRow("Typing Speed:", self.typing_speed_spin)

        # Chunk size
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(10, 1000)
        self.chunk_size_spin.setSuffix(" chars")
        self.chunk_size_spin.setToolTip("Size of text chunks for typing (10-1000 characters)")
        typing_layout.addRow("Chunk Size:", self.chunk_size_spin)

        # Adaptive delay
        self.adaptive_delay_checkbox = QCheckBox()
        self.adaptive_delay_checkbox.setToolTip("Automatically adjust typing speed based on system load")
        typing_layout.addRow("Adaptive Delay:", self.adaptive_delay_checkbox)

        typing_group.setLayout(typing_layout)
        layout.addWidget(typing_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Performance")

    def _create_history_tab(self) -> None:
        """Create the history settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # History settings group
        history_group = QGroupBox("History Settings")
        history_layout = QFormLayout()

        # History size
        self.history_size_spin = QSpinBox()
        self.history_size_spin.setRange(1, 10000)
        self.history_size_spin.setSuffix(" entries")
        self.history_size_spin.setToolTip("Maximum number of clipboard entries to keep (1-10000)")
        history_layout.addRow("History Size:", self.history_size_spin)

        # Retention days
        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(0, 365)
        self.retention_days_spin.setSuffix(" days")
        self.retention_days_spin.setSpecialValueText("Forever")
        self.retention_days_spin.setToolTip("How long to keep history entries (0 for forever)")
        history_layout.addRow("Retention:", self.retention_days_spin)

        # Encrypt sensitive
        self.encrypt_sensitive_checkbox = QCheckBox()
        self.encrypt_sensitive_checkbox.setToolTip("Encrypt clipboard entries that may contain sensitive data")
        history_layout.addRow("Encrypt Sensitive:", self.encrypt_sensitive_checkbox)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "History")

    def _create_general_tab(self) -> None:
        """Create the general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # General settings group
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()

        # Paste mode
        self.paste_mode_combo = QComboBox()
        self.paste_mode_combo.addItems(["Auto", "Clipboard", "Typing"])
        self.paste_mode_combo.setToolTip("Default paste method")
        general_layout.addRow("Paste Mode:", self.paste_mode_combo)

        # Monitoring enabled
        self.monitoring_enabled_checkbox = QCheckBox()
        self.monitoring_enabled_checkbox.setToolTip("Enable clipboard monitoring")
        general_layout.addRow("Monitoring Enabled:", self.monitoring_enabled_checkbox)

        # Start on login
        self.start_on_login_checkbox = QCheckBox()
        self.start_on_login_checkbox.setToolTip("Start Pasta when you log in")
        general_layout.addRow("Start on Login:", self.start_on_login_checkbox)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "General")

    def _create_privacy_tab(self) -> None:
        """Create the privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Privacy settings group
        privacy_group = QGroupBox("Privacy Settings")
        privacy_layout = QFormLayout()

        # Privacy mode
        self.privacy_mode_checkbox = QCheckBox()
        self.privacy_mode_checkbox.setToolTip("Temporarily disable all clipboard monitoring")
        privacy_layout.addRow("Privacy Mode:", self.privacy_mode_checkbox)

        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)

        # Excluded apps group
        excluded_group = QGroupBox("Excluded Applications")
        excluded_layout = QVBoxLayout()

        # Input for new app
        input_layout = QHBoxLayout()
        self.excluded_app_input = QLineEdit()
        self.excluded_app_input.setPlaceholderText("Enter application name...")
        input_layout.addWidget(self.excluded_app_input)

        self.add_excluded_app_button = QPushButton("Add")
        self.add_excluded_app_button.clicked.connect(self._add_excluded_app)
        input_layout.addWidget(self.add_excluded_app_button)

        excluded_layout.addLayout(input_layout)

        # List of excluded apps
        self.excluded_apps_list = QListWidget()
        excluded_layout.addWidget(self.excluded_apps_list)

        # Remove button
        self.remove_excluded_app_button = QPushButton("Remove Selected")
        self.remove_excluded_app_button.clicked.connect(self._remove_excluded_app)
        excluded_layout.addWidget(self.remove_excluded_app_button)

        excluded_group.setLayout(excluded_layout)
        layout.addWidget(excluded_group)

        self.tab_widget.addTab(tab, "Privacy")

    def _create_hotkeys_tab(self) -> None:
        """Create the hotkeys settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Hotkeys group
        hotkeys_group = QGroupBox("Hotkey Configuration")
        hotkeys_layout = QFormLayout()

        # Emergency stop
        self.emergency_stop_hotkey_input = QLineEdit()
        self.emergency_stop_hotkey_input.setToolTip("Hotkey to stop pasting immediately")
        hotkeys_layout.addRow("Emergency Stop:", self.emergency_stop_hotkey_input)

        # Quick paste
        self.quick_paste_hotkey_input = QLineEdit()
        self.quick_paste_hotkey_input.setToolTip("Hotkey to paste last clipboard item")
        hotkeys_layout.addRow("Quick Paste:", self.quick_paste_hotkey_input)

        # Toggle monitoring
        self.toggle_monitoring_hotkey_input = QLineEdit()
        self.toggle_monitoring_hotkey_input.setToolTip("Hotkey to toggle clipboard monitoring")
        hotkeys_layout.addRow("Toggle Monitoring:", self.toggle_monitoring_hotkey_input)

        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        # Instructions
        instructions = QLabel(
            "Enter hotkeys in the format: ctrl+shift+v\nAvailable modifiers: ctrl, shift, alt, cmd/win\nLeave empty to disable a hotkey."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Hotkeys")

    def _connect_change_tracking(self) -> None:
        """Connect signals for tracking changes."""
        # Spin boxes
        for spin in [self.typing_speed_spin, self.chunk_size_spin, self.history_size_spin, self.retention_days_spin]:
            spin.valueChanged.connect(self._on_setting_changed)

        # Checkboxes
        for checkbox in [
            self.adaptive_delay_checkbox,
            self.encrypt_sensitive_checkbox,
            self.monitoring_enabled_checkbox,
            self.start_on_login_checkbox,
            self.privacy_mode_checkbox,
        ]:
            checkbox.toggled.connect(self._on_setting_changed)

        # Combo box
        self.paste_mode_combo.currentIndexChanged.connect(self._on_setting_changed)

        # Line edits
        for line_edit in [self.emergency_stop_hotkey_input, self.quick_paste_hotkey_input, self.toggle_monitoring_hotkey_input]:
            line_edit.textChanged.connect(self._on_setting_changed)

    def _on_setting_changed(self) -> None:
        """Handle any setting change."""
        self._has_changes = True
        self.settings_changed.emit()

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes.

        Returns:
            True if there are unsaved changes
        """
        return self._has_changes

    def load_settings(self) -> None:
        """Load current settings into UI."""
        settings = self.settings_manager.settings

        # Performance
        self.typing_speed_spin.setValue(settings.typing_speed)
        self.chunk_size_spin.setValue(settings.chunk_size)
        self.adaptive_delay_checkbox.setChecked(settings.adaptive_delay)

        # History
        self.history_size_spin.setValue(settings.history_size)
        self.retention_days_spin.setValue(settings.history_retention_days)
        self.encrypt_sensitive_checkbox.setChecked(settings.encrypt_sensitive)

        # General
        paste_mode_index = {"auto": 0, "clipboard": 1, "typing": 2}.get(settings.paste_mode, 0)
        self.paste_mode_combo.setCurrentIndex(paste_mode_index)
        self.monitoring_enabled_checkbox.setChecked(settings.monitoring_enabled)
        self.start_on_login_checkbox.setChecked(settings.start_on_login)

        # Privacy
        self.privacy_mode_checkbox.setChecked(settings.privacy_mode)
        self.excluded_apps_list.clear()
        self.excluded_apps_list.addItems(settings.excluded_apps)

        # Hotkeys
        self.emergency_stop_hotkey_input.setText(settings.emergency_stop_hotkey)
        self.quick_paste_hotkey_input.setText(settings.quick_paste_hotkey)
        self.toggle_monitoring_hotkey_input.setText(settings.toggle_monitoring_hotkey)

        # Reset change tracking
        self._has_changes = False

    def gather_settings(self) -> dict:
        """Gather current settings from UI.

        Returns:
            Dictionary of settings
        """
        # Get excluded apps
        excluded_apps = []
        for i in range(self.excluded_apps_list.count()):
            item = self.excluded_apps_list.item(i)
            if item is not None:
                excluded_apps.append(item.text())

        return {
            # Performance
            "typing_speed": self.typing_speed_spin.value(),
            "chunk_size": self.chunk_size_spin.value(),
            "adaptive_delay": self.adaptive_delay_checkbox.isChecked(),
            # History
            "history_size": self.history_size_spin.value(),
            "history_retention_days": self.retention_days_spin.value(),
            "encrypt_sensitive": self.encrypt_sensitive_checkbox.isChecked(),
            # General
            "paste_mode": self.paste_mode_combo.currentText().lower(),
            "monitoring_enabled": self.monitoring_enabled_checkbox.isChecked(),
            "start_on_login": self.start_on_login_checkbox.isChecked(),
            # Privacy
            "privacy_mode": self.privacy_mode_checkbox.isChecked(),
            "excluded_apps": excluded_apps,
            # Hotkeys
            "emergency_stop_hotkey": self.emergency_stop_hotkey_input.text(),
            "quick_paste_hotkey": self.quick_paste_hotkey_input.text(),
            "toggle_monitoring_hotkey": self.toggle_monitoring_hotkey_input.text(),
        }

    def save_settings(self) -> None:
        """Save settings and close window."""
        self.apply_settings()
        self.close()

    def apply_settings(self) -> None:
        """Apply settings without closing."""
        try:
            settings = self.gather_settings()
            self.settings_manager.update(**settings)
            self._has_changes = False
            self.original_settings = self.settings_manager.settings.copy()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Settings", str(e))

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_settings()

    def _add_excluded_app(self) -> None:
        """Add app to excluded list."""
        app_name = self.excluded_app_input.text().strip()
        existing_apps = []
        for i in range(self.excluded_apps_list.count()):
            item = self.excluded_apps_list.item(i)
            if item is not None:
                existing_apps.append(item.text())

        if app_name and app_name not in existing_apps:
            self.excluded_apps_list.addItem(app_name)
            self.excluded_app_input.clear()
            self._on_setting_changed()

    def _remove_excluded_app(self) -> None:
        """Remove selected app from excluded list."""
        current_item = self.excluded_apps_list.currentItem()
        if current_item:
            self.excluded_apps_list.takeItem(self.excluded_apps_list.row(current_item))
            self._on_setting_changed()

    def close_event(self, event: Any) -> None:
        """Handle window close event."""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()
