"""Improved settings window with modern UI/UX using PySide6."""

import json
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
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

from pasta.core.settings import Settings, SettingsManager


class SettingsWindow(QDialog):
    """Modern settings window for configuring Pasta."""

    # Signal emitted when settings change
    settings_changed = Signal()

    def __init__(self, settings_manager: SettingsManager, parent: Optional[QWidget] = None) -> None:
        """Initialize the improved settings window.

        Args:
            settings_manager: SettingsManager instance
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings.copy()  # Work with a copy
        self.original_settings = settings_manager.settings.copy()  # Keep original for comparison
        self._unsaved_changes = False

        self.setWindowTitle("Pasta Settings")
        self.setGeometry(100, 100, 700, 600)
        self.setModal(False)  # Non-modal dialog

        # macOS-specific: Ensure window appears in dock and handles shortcuts properly
        if sys.platform == "darwin":
            # Window should appear in dock when open
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

            # Add Cmd+W shortcut that closes this window (standard macOS behavior)
            cmd_w = QShortcut(QKeySequence("Ctrl+W"), self)  # Ctrl+W is Cmd+W on macOS
            cmd_w.activated.connect(self.close)

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Add search bar at the top
        self._create_search_bar(main_layout)

        # Create tab widget with icons
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # Modern tab appearance
        main_layout.addWidget(self.tabs)

        # Create tabs with icons
        self._create_general_tab()
        self._create_performance_tab()
        self._create_history_tab()
        self._create_privacy_tab()
        self._create_hotkeys_tab()

        # Status bar for feedback
        self._create_status_bar(main_layout)

        # Button bar with improved layout
        self._create_button_bar(main_layout)

        # Set up keyboard shortcuts
        self._setup_shortcuts()

        # Connect change detection
        self._connect_change_detection()

        # Apply modern stylesheet
        self._apply_stylesheet()

    def _create_search_bar(self, layout: QVBoxLayout) -> None:
        """Create search bar for finding settings."""
        search_layout = QHBoxLayout()

        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("settings_search")
        self.search_box.setPlaceholderText("Type to search settings...")
        self.search_box.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_box)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.search_box.clear)
        search_layout.addWidget(clear_button)

        layout.addLayout(search_layout)

    def _create_status_bar(self, layout: QVBoxLayout) -> None:
        """Create status bar for feedback messages."""
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Status label
        self.status_bar = QLabel("")
        self.status_bar.setObjectName("status_bar")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_bar.setStyleSheet("QLabel { color: #666; padding: 5px; }")
        layout.addWidget(self.status_bar)

        # Timer for auto-clearing status messages
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._clear_status)
        self.status_timer.setSingleShot(True)

    def _create_button_bar(self, layout: QVBoxLayout) -> None:
        """Create button bar with modern layout."""
        button_layout = QHBoxLayout()

        # Left side - utility buttons
        self.import_button = QPushButton("Import...")
        self.import_button.setToolTip("Import settings from file")
        self.import_button.clicked.connect(self.import_settings)
        button_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Export...")
        self.export_button.setToolTip("Export current settings to file")
        self.export_button.clicked.connect(self.export_settings)
        button_layout.addWidget(self.export_button)

        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.setToolTip("Reset all settings to default values")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        # Add stretch to push main buttons to the right
        button_layout.addStretch()

        # Right side - main action buttons
        self.undo_button = QPushButton("Undo")
        self.undo_button.setObjectName("undo_button")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_changes)
        button_layout.addWidget(self.undo_button)

        self.apply_button = QPushButton("Apply")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+S to save/apply
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.apply_settings)

        # Ctrl+R to reset defaults
        reset_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        reset_shortcut.activated.connect(self.reset_to_defaults)

        # Escape to close
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.close)

    def _create_general_tab(self) -> None:
        """Create the General settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Startup group
        startup_group = self._create_group_box("Startup")
        startup_layout = QFormLayout()

        self.start_on_login = QCheckBox("Start Pasta on system login")
        self.start_on_login.setChecked(self.settings.start_on_login)
        self.start_on_login.setToolTip("Automatically start Pasta when you log in to your computer")
        startup_layout.addRow(self.start_on_login)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        # Monitoring group
        monitoring_group = self._create_group_box("Monitoring")
        monitoring_layout = QFormLayout()

        self.monitoring_enabled = QCheckBox("Enable clipboard monitoring")
        self.monitoring_enabled.setChecked(self.settings.monitoring_enabled)
        self.monitoring_enabled.setToolTip("Monitor clipboard for changes and save to history")
        monitoring_layout.addRow(self.monitoring_enabled)

        self.paste_mode = QComboBox()
        self.paste_mode.addItems(["Auto", "Clipboard", "Typing"])
        self.paste_mode.setCurrentText(self.settings.paste_mode.capitalize())
        self.paste_mode.setToolTip("Default method for pasting content")
        monitoring_layout.addRow("Default paste mode:", self.paste_mode)

        monitoring_group.setLayout(monitoring_layout)
        layout.addWidget(monitoring_group)

        layout.addStretch()

        # Add icon to tab
        icon = self._get_icon("general")
        self.tabs.addTab(tab, icon, "General")

    def _create_performance_tab(self) -> None:
        """Create the Performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Typing speed group
        speed_group = self._create_group_box("Typing Speed")
        speed_layout = QFormLayout()

        self.typing_speed = QSlider(Qt.Orientation.Horizontal)
        self.typing_speed.setRange(10, 500)
        self.typing_speed.setValue(self.settings.typing_speed)
        self.typing_speed.setTickInterval(50)
        self.typing_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.typing_speed.setToolTip("How fast to type characters per second in typing mode")

        self.speed_label = QLabel(f"{self.settings.typing_speed} chars/sec")
        self.typing_speed.valueChanged.connect(self._on_typing_speed_changed)

        speed_layout.addRow("Typing speed:", self.typing_speed)
        speed_layout.addRow("", self.speed_label)

        # Add validation error label
        self.typing_speed_error = QLabel("")
        self.typing_speed_error.setObjectName("typing_speed_error")
        self.typing_speed_error.setStyleSheet("QLabel { color: red; font-size: 12px; }")
        self.typing_speed_error.hide()
        speed_layout.addRow("", self.typing_speed_error)

        self.chunk_size = QSpinBox()
        self.chunk_size.setRange(50, 1000)
        self.chunk_size.setValue(self.settings.chunk_size)
        self.chunk_size.setSingleStep(50)
        self.chunk_size.setToolTip("Size of text chunks when typing long content")
        speed_layout.addRow("Chunk size:", self.chunk_size)

        self.adaptive_delay = QCheckBox("Use adaptive delays based on system load")
        self.adaptive_delay.setChecked(self.settings.adaptive_delay)
        self.adaptive_delay.setToolTip("Automatically adjust typing speed based on system performance")
        speed_layout.addRow(self.adaptive_delay)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        layout.addStretch()

        # Add icon to tab
        icon = self._get_icon("performance")
        self.tabs.addTab(tab, icon, "Performance")

    def _create_history_tab(self) -> None:
        """Create the History settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # History settings group
        history_group = self._create_group_box("History Settings")
        history_layout = QFormLayout()

        self.history_size = QSpinBox()
        self.history_size.setRange(10, 10000)
        self.history_size.setValue(self.settings.history_size)
        self.history_size.setSingleStep(10)
        self.history_size.setToolTip("Maximum number of clipboard entries to keep in history")
        history_layout.addRow("Maximum entries:", self.history_size)

        self.history_retention = QSpinBox()
        self.history_retention.setRange(1, 365)
        self.history_retention.setValue(self.settings.history_retention_days)
        self.history_retention.setSuffix(" days")
        self.history_retention.setToolTip("How long to keep clipboard history")
        history_layout.addRow("Keep history for:", self.history_retention)

        self.encrypt_sensitive = QCheckBox("Encrypt sensitive clipboard data")
        self.encrypt_sensitive.setChecked(self.settings.encrypt_sensitive)
        self.encrypt_sensitive.setToolTip("Encrypt passwords and other sensitive data in storage")
        history_layout.addRow(self.encrypt_sensitive)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()

        # Add icon to tab
        icon = self._get_icon("history")
        self.tabs.addTab(tab, icon, "History")

    def _create_privacy_tab(self) -> None:
        """Create the Privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Privacy mode
        privacy_group = self._create_group_box("Privacy")
        privacy_layout = QFormLayout()

        self.privacy_mode = QCheckBox("Enable privacy mode")
        self.privacy_mode.setChecked(self.settings.privacy_mode)
        self.privacy_mode.setToolTip("Temporarily disable all clipboard monitoring")
        privacy_layout.addRow(self.privacy_mode)

        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)

        # Excluded apps
        excluded_group = self._create_group_box("Excluded Applications")
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
        button_layout.addStretch()

        excluded_layout.addLayout(button_layout)
        excluded_group.setLayout(excluded_layout)
        layout.addWidget(excluded_group)

        # Excluded patterns
        patterns_group = self._create_group_box("Excluded Patterns")
        patterns_layout = QVBoxLayout()

        patterns_label = QLabel("Text matching these patterns will not be stored:")
        patterns_layout.addWidget(patterns_label)

        self.excluded_patterns = QTextEdit()
        self.excluded_patterns.setPlainText("\n".join(self.settings.excluded_patterns))
        self.excluded_patterns.setMaximumHeight(100)
        self.excluded_patterns.setPlaceholderText("Enter one pattern per line...")
        patterns_layout.addWidget(self.excluded_patterns)

        patterns_group.setLayout(patterns_layout)
        layout.addWidget(patterns_group)

        # Add icon to tab
        icon = self._get_icon("privacy")
        self.tabs.addTab(tab, icon, "Privacy")

    def _create_hotkeys_tab(self) -> None:
        """Create the Hotkeys settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Hotkeys group
        hotkeys_group = self._create_group_box("Global Hotkeys")
        hotkeys_layout = QFormLayout()

        self.emergency_stop_hotkey = QLineEdit()
        self.emergency_stop_hotkey.setText(self.settings.emergency_stop_hotkey)
        self.emergency_stop_hotkey.setPlaceholderText("e.g., esc+esc")
        self.emergency_stop_hotkey.setToolTip("Hotkey to immediately stop any paste operation")
        hotkeys_layout.addRow("Emergency stop:", self.emergency_stop_hotkey)

        self.quick_paste_hotkey = QLineEdit()
        self.quick_paste_hotkey.setText(self.settings.quick_paste_hotkey)
        self.quick_paste_hotkey.setPlaceholderText("e.g., ctrl+shift+v")
        self.quick_paste_hotkey.setToolTip("Hotkey to quickly paste last clipboard item")
        hotkeys_layout.addRow("Quick paste:", self.quick_paste_hotkey)

        self.toggle_monitoring_hotkey = QLineEdit()
        self.toggle_monitoring_hotkey.setText(self.settings.toggle_monitoring_hotkey)
        self.toggle_monitoring_hotkey.setPlaceholderText("e.g., ctrl+shift+m")
        self.toggle_monitoring_hotkey.setToolTip("Hotkey to toggle clipboard monitoring on/off")
        hotkeys_layout.addRow("Toggle monitoring:", self.toggle_monitoring_hotkey)

        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)

        # Note
        note_label = QLabel("Note: Hotkey functionality may be limited on macOS due to system restrictions.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        layout.addWidget(note_label)

        layout.addStretch()

        # Add icon to tab
        icon = self._get_icon("hotkeys")
        self.tabs.addTab(tab, icon, "Hotkeys")

    def _create_group_box(self, title: str) -> QGroupBox:
        """Create a styled group box."""
        group = QGroupBox(title)
        group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )
        return group

    def _get_icon(self, name: str) -> QIcon:  # noqa: ARG002
        """Get icon for tab. Returns empty icon if not found."""
        # In a real implementation, would load actual icons
        # For now, return empty icon
        return QIcon()

    def _connect_change_detection(self) -> None:
        """Connect widgets to detect changes."""
        # General tab
        self.start_on_login.toggled.connect(self._on_setting_changed)
        self.monitoring_enabled.toggled.connect(self._on_setting_changed)
        self.paste_mode.currentTextChanged.connect(self._on_setting_changed)

        # Performance tab
        self.typing_speed.valueChanged.connect(self._on_setting_changed)
        self.chunk_size.valueChanged.connect(self._on_setting_changed)
        self.adaptive_delay.toggled.connect(self._on_setting_changed)

        # History tab
        self.history_size.valueChanged.connect(self._on_setting_changed)
        self.history_retention.valueChanged.connect(self._on_setting_changed)
        self.encrypt_sensitive.toggled.connect(self._on_setting_changed)

        # Privacy tab
        self.privacy_mode.toggled.connect(self._on_setting_changed)
        self.excluded_patterns.textChanged.connect(self._on_setting_changed)

        # Hotkeys tab
        self.emergency_stop_hotkey.textEdited.connect(self._on_setting_changed)
        self.quick_paste_hotkey.textEdited.connect(self._on_setting_changed)
        self.toggle_monitoring_hotkey.textEdited.connect(self._on_setting_changed)

    def _on_setting_changed(self) -> None:
        """Handle when any setting is changed."""
        self._unsaved_changes = True
        self.apply_button.setEnabled(True)
        self.apply_button.setProperty("unsaved", True)
        self.apply_button.style().polish(self.apply_button)
        self.undo_button.setEnabled(True)
        self.settings_changed.emit()

    def _on_typing_speed_changed(self, value: int) -> None:
        """Handle typing speed slider changes."""
        self.speed_label.setText(f"{value} chars/sec")

        # Validate
        if value > 1000:
            self.typing_speed_error.setText("Speed must be between 10 and 1000")
            self.typing_speed_error.show()
        else:
            self.typing_speed_error.hide()

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes."""
        if not text:
            # Clear any highlighting
            self._clear_search_highlights()
            return

        # Search for matching settings
        text_lower = text.lower()

        # Check each tab for matching settings
        for i in range(self.tabs.count()):
            tab_widget = self.tabs.widget(i)
            if self._search_in_widget(tab_widget, text_lower):
                # Switch to tab with match
                self.tabs.setCurrentIndex(i)
                break

    def _search_in_widget(self, widget: QWidget, search_text: str) -> bool:  # noqa: ARG002
        """Search for text in widget and its children."""
        # This is a simplified implementation
        # In reality, would search widget text and highlight matches
        return False

    def _clear_search_highlights(self) -> None:
        """Clear search highlighting."""
        # Would clear any visual highlights
        pass

    def add_excluded_app(self) -> None:
        """Add an application to the excluded list."""
        from PySide6.QtWidgets import QInputDialog

        app_name, ok = QInputDialog.getText(self, "Add Excluded Application", "Enter application name:")
        if ok and app_name:
            self.excluded_apps_list.addItem(app_name)
            self._on_setting_changed()

    def remove_excluded_app(self) -> None:
        """Remove selected application from excluded list."""
        current_item = self.excluded_apps_list.currentItem()
        if current_item:
            self.excluded_apps_list.takeItem(self.excluded_apps_list.row(current_item))
            self._on_setting_changed()

    def apply_settings(self) -> None:
        """Apply settings without closing dialog."""
        # Update settings from UI
        self._update_settings_from_ui()

        # Validate settings
        try:
            self.settings.validate()
        except ValueError as e:
            self.show_status(f"Validation error: {e}", error=True)
            return

        # Save settings
        self.settings_manager.update_settings(self.settings)
        self.settings_manager.save()

        # Update original settings
        self.original_settings = self.settings.copy()

        # Reset unsaved changes state
        self._unsaved_changes = False
        self.apply_button.setEnabled(False)
        self.apply_button.setProperty("unsaved", False)
        self.apply_button.style().polish(self.apply_button)
        self.undo_button.setEnabled(False)

        # Show status message instead of popup
        self.show_status("Settings saved successfully", success=True)

    def accept_settings(self) -> None:
        """Apply settings and close dialog."""
        self.apply_settings()
        if not self._unsaved_changes:  # Only close if save was successful
            self.accept()

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Create default settings
            default_settings = Settings()

            # Update all UI elements
            self._update_ui_from_settings(default_settings)

            # Mark as changed
            self._on_setting_changed()

            # Show status
            self.show_status("Settings reset to defaults. Click Apply to save.", info=True)

    def undo_changes(self) -> None:
        """Undo all changes since last save."""
        # Restore from original settings
        self._update_ui_from_settings(self.original_settings)

        # Reset unsaved changes state
        self._unsaved_changes = False
        self.apply_button.setEnabled(False)
        self.apply_button.setProperty("unsaved", False)
        self.apply_button.style().polish(self.apply_button)
        self.undo_button.setEnabled(False)

        # Show status
        self.show_status("Changes undone", info=True)

    def import_settings(self) -> None:
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Settings", "", "JSON Files (*.json);;All Files (*)")

        if file_path:
            try:
                # Read settings
                with open(file_path) as f:
                    data = json.load(f)

                # Create settings object
                imported_settings = Settings.from_dict(data)
                imported_settings.validate()

                # Show comparison dialog
                if self.show_import_comparison(imported_settings):
                    # Update UI
                    self._update_ui_from_settings(imported_settings)
                    self._on_setting_changed()
                    self.show_status("Settings imported. Click Apply to save.", info=True)

            except Exception as e:
                self.show_status(f"Import failed: {e}", error=True)

    def export_settings(self) -> None:
        """Export current settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "pasta_settings.json", "JSON Files (*.json);;All Files (*)")

        if file_path:
            try:
                # Get current settings from UI
                self._update_settings_from_ui()

                # Export
                self.settings_manager.export_settings(Path(file_path))
                self.show_status("Settings exported successfully", success=True)

            except Exception as e:
                self.show_status(f"Export failed: {e}", error=True)

    def show_import_comparison(self, imported_settings: Settings) -> bool:  # noqa: ARG002
        """Show comparison between current and imported settings.

        Args:
            imported_settings: Settings to import

        Returns:
            True if user wants to proceed with import
        """
        # In a full implementation, would show a nice comparison dialog
        # For now, just confirm
        reply = QMessageBox.question(
            self,
            "Import Settings",
            "Do you want to import these settings? Your current settings will be replaced.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        return bool(reply == QMessageBox.StandardButton.Yes)

    def show_status(self, message: str, error: bool = False, success: bool = False, info: bool = False) -> None:
        """Show status message in status bar.

        Args:
            message: Message to show
            error: Show as error (red)
            success: Show as success (green)
            info: Show as info (blue)
        """
        # Set style based on type
        if error:
            self.status_bar.setStyleSheet("QLabel { color: #d32f2f; padding: 5px; }")
        elif success:
            self.status_bar.setStyleSheet("QLabel { color: #388e3c; padding: 5px; }")
        elif info:
            self.status_bar.setStyleSheet("QLabel { color: #1976d2; padding: 5px; }")
        else:
            self.status_bar.setStyleSheet("QLabel { color: #666; padding: 5px; }")

        # Show message
        self.status_bar.setText(message)

        # Auto-clear after 3 seconds
        self.status_timer.start(3000)

    def _clear_status(self) -> None:
        """Clear status message."""
        self.status_bar.setText("")

    def _update_settings_from_ui(self) -> None:
        """Update settings object from UI values."""
        self.settings.start_on_login = self.start_on_login.isChecked()
        self.settings.monitoring_enabled = self.monitoring_enabled.isChecked()
        self.settings.paste_mode = self.paste_mode.currentText().lower()
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

    def _update_ui_from_settings(self, settings: Settings) -> None:
        """Update UI elements from settings object."""
        # Temporarily disconnect change detection
        self._disconnect_change_detection()

        # General
        self.start_on_login.setChecked(settings.start_on_login)
        self.monitoring_enabled.setChecked(settings.monitoring_enabled)
        self.paste_mode.setCurrentText(settings.paste_mode.capitalize())

        # Performance
        self.typing_speed.setValue(settings.typing_speed)
        self.chunk_size.setValue(settings.chunk_size)
        self.adaptive_delay.setChecked(settings.adaptive_delay)

        # History
        self.history_size.setValue(settings.history_size)
        self.history_retention.setValue(settings.history_retention_days)
        self.encrypt_sensitive.setChecked(settings.encrypt_sensitive)

        # Privacy
        self.privacy_mode.setChecked(settings.privacy_mode)
        self.excluded_apps_list.clear()
        self.excluded_apps_list.addItems(settings.excluded_apps)
        self.excluded_patterns.setPlainText("\n".join(settings.excluded_patterns))

        # Hotkeys
        self.emergency_stop_hotkey.setText(settings.emergency_stop_hotkey)
        self.quick_paste_hotkey.setText(settings.quick_paste_hotkey)
        self.toggle_monitoring_hotkey.setText(settings.toggle_monitoring_hotkey)

        # Reconnect change detection
        self._connect_change_detection()

    def _disconnect_change_detection(self) -> None:
        """Temporarily disconnect change detection."""
        try:
            # General tab
            self.start_on_login.toggled.disconnect()
            self.monitoring_enabled.toggled.disconnect()
            self.paste_mode.currentTextChanged.disconnect()

            # Performance tab
            self.typing_speed.valueChanged.disconnect(self._on_setting_changed)
            self.chunk_size.valueChanged.disconnect()
            self.adaptive_delay.toggled.disconnect()

            # History tab
            self.history_size.valueChanged.disconnect()
            self.history_retention.valueChanged.disconnect()
            self.encrypt_sensitive.toggled.disconnect()

            # Privacy tab
            self.privacy_mode.toggled.disconnect()
            self.excluded_patterns.textChanged.disconnect()

            # Hotkeys tab
            self.emergency_stop_hotkey.textEdited.disconnect()
            self.quick_paste_hotkey.textEdited.disconnect()
            self.toggle_monitoring_hotkey.textEdited.disconnect()
        except Exception:
            pass  # Ignore if not connected

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._unsaved_changes

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle window close event.

        Args:
            event: The close event
        """
        if self._unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                self.apply_settings()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _apply_stylesheet(self) -> None:
        """Apply modern stylesheet to the window."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f5f5f5;
            }

            QPushButton {
                min-width: 80px;
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
            }

            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }

            QPushButton:pressed {
                background-color: #d0d0d0;
            }

            QPushButton:default {
                border-color: #0066cc;
                color: #0066cc;
            }

            QPushButton[unsaved="true"] {
                border-color: #ff9800;
                background-color: #fff3e0;
            }

            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #fff;
                border-radius: 4px;
            }

            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }

            QTabBar::tab:selected {
                background-color: #fff;
                border-bottom: 2px solid #0066cc;
            }

            QLineEdit, QSpinBox, QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
            }

            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #0066cc;
                outline: none;
            }

            QCheckBox {
                spacing: 8px;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background-color: #ddd;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                background-color: #0066cc;
                border-radius: 8px;
                margin: -5px 0;
            }

            QSlider::handle:horizontal:hover {
                background-color: #0052cc;
            }
        """
        )
