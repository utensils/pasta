# macOS UI/UX Improvements

This document describes the macOS-specific UI/UX improvements implemented for Pasta.

## Overview

The improvements ensure Pasta behaves as a proper macOS menu bar application:
- No dock icon when running (menu bar only)
- Proper app name "Pasta" instead of "python3.11"
- Dialog windows appear in dock when open
- Cmd+Q on dialogs closes only the window, not the entire app

## Implementation Details

### 1. LSUIElement Configuration

The app is configured to run as a background application (agent) using `LSUIElement`:

**PyInstaller Spec (pasta.spec):**
```python
info_plist = {
    'LSUIElement': True,  # Run as agent app (no dock icon)
    'CFBundleName': 'Pasta',
    'CFBundleDisplayName': 'Pasta',
    'CFBundleIdentifier': 'com.utensils.pasta',
    ...
}
```

### 2. Application Configuration

**System Tray Initialization (tray_pyside6.py):**
```python
# Set application name so dialogs show "Pasta" instead of "python"
self._app.setApplicationName("Pasta")
self._app.setApplicationDisplayName("Pasta")
self._app.setOrganizationName("Utensils")
self._app.setOrganizationDomain("utensils.dev")

# Don't quit when last window is closed (we're a tray app)
self._app.setQuitOnLastWindowClosed(False)

# macOS-specific: Try to set accessory policy
if sys.platform == "darwin":
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )
    except ImportError:
        pass  # Will rely on Info.plist LSUIElement
```

### 3. Window Behavior

**Settings and History Windows:**
- Non-modal dialogs that appear in the dock when open
- Cmd+Q shortcut that closes only the window
- Proper window titles and organization

```python
# macOS-specific: Ensure window appears in dock and handles Cmd+Q properly
if sys.platform == "darwin":
    # Window should appear in dock when open
    self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)

    # Add Cmd+Q shortcut that only closes this window
    cmd_q = QShortcut(QKeySequence("Ctrl+Q"), self)  # Ctrl+Q is Cmd+Q on macOS
    cmd_q.activated.connect(self.close)
```

## Building for macOS

Use the provided build script:

```bash
./scripts/build_macos.sh
```

This will:
1. Install dependencies
2. Run tests
3. Build the app bundle with PyInstaller
4. Create `dist/Pasta.app`

## Installation

After building:
```bash
cp -r dist/Pasta.app /Applications/
```

## Running

- **From Terminal:** `open /Applications/Pasta.app`
- **From Finder:** Double-click Pasta in Applications
- **From Spotlight:** Search for "Pasta"

## Testing

Run the macOS-specific tests:
```bash
uv run pytest tests/unit/test_macos_ui_simple.py
uv run pytest tests/integration/test_macos_ui_integration.py
```

## User Experience

1. **Launch:** App starts in menu bar only (no dock icon)
2. **Settings/History:** Windows appear in dock with "Pasta" name
3. **Cmd+Q:** Closes current window only, app continues running
4. **Menu Bar:** Right-click for options, left-click for emergency stop

## Known Issues

- PyObjC is optional; if not installed, relies on Info.plist settings
- App bundle required for full LSUIElement behavior
- Development mode (running via `python`) may show dock icon

## Future Improvements

- Custom menu bar icon
- Native macOS notifications
- Touch Bar support (if applicable)
- Handoff/Continuity integration
