# Pasta - Current State

## Overview

Pasta is a clipboard history manager that monitors everything you copy and saves it for later use. It no longer automatically pastes content - instead, it builds a searchable history that users can manually access.

## Core Functionality

### What Pasta Does

1. **Monitors Clipboard**: Detects when you copy text (Ctrl+C/Cmd+C)
2. **Saves to History**: Stores all clipboard content in an encrypted SQLite database
3. **Provides History UI**: Searchable window to view past clipboard items
4. **Enables Manual Paste**: Users can copy items from history back to clipboard

### What Pasta Does NOT Do

1. **No Auto-Paste**: Copying text does not trigger automatic typing
2. **No Interference**: Normal copy/paste operations work as expected
3. **No Network Access**: All data stays local

## User Workflow

1. **Launch Pasta**: Runs in system tray
2. **Copy Normally**: Use Ctrl+C/Cmd+C as usual - content is saved automatically
3. **View History**: Right-click tray → History
4. **Search History**: Use search box to find past items
5. **Reuse Content**: Select item → "Copy to Clipboard" button

## Platform-Specific Features

### macOS
- Runs as menu bar app (no dock icon)
- Dialog windows show "Pasta" in dock when open
- Cmd+W closes windows
- Cmd+Q closes windows (not quit app)
- Native window controls

### Windows
- System tray icon
- May require admin privileges for some apps

### Linux
- System tray support varies by desktop environment
- Requires user in 'input' group

## Security & Privacy

- **Encryption**: Sensitive data (passwords, API keys) encrypted at rest
- **Pattern Detection**: Automatically identifies sensitive content
- **Privacy Mode**: Can temporarily disable monitoring
- **App Exclusion**: Can exclude specific applications
- **Local Only**: No cloud sync or network features

## Settings

- **Monitoring Enabled**: Toggle clipboard monitoring
- **Paste Mode**: Future use for manual paste triggers
- **History Size**: How many items to keep
- **Auto-Clear**: Automatic history cleanup
- **Sensitive Data**: Detection and encryption settings
- **Hotkeys**: Emergency stop, future quick paste

## Known Limitations

1. **Manual Paste Only**: No automatic typing (by design)
2. **Text Only**: Currently handles text content
3. **No Image Support**: Images in clipboard not saved
4. **No Cloud Sync**: Local storage only

## Future Features

1. **Quick Paste Hotkey**: Global hotkey to paste from history
2. **Snippet Templates**: Save frequently used text
3. **Format Support**: Rich text, images, files
4. **Export/Import**: Backup and restore history
5. **Categories**: Organize clipboard items

## Technical Details

- **Language**: Python 3.9+
- **UI Framework**: PySide6 (Qt)
- **Storage**: SQLite with Fernet encryption
- **Clipboard**: pyperclip for cross-platform support
- **Keyboard**: PyAutoGUI for future paste features

## Building & Distribution

- **Development**: `uv run python -m pasta`
- **macOS**: `./scripts/build_macos.sh` creates .app bundle
- **Windows/Linux**: `uv run pyinstaller pasta.spec`
- **Package**: `uv build` creates wheel/sdist

## Testing

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: UI and workflow tests
- **Regression Tests**: Clipboard monitoring behavior
- **Platform Tests**: macOS, Windows, Linux CI/CD

## Recent Changes

1. **Fixed Auto-Paste Bug**: Clipboard monitoring no longer triggers paste
2. **Fixed History Saving**: All copied content now saved properly
3. **macOS UI Improvements**: Proper app behavior and window handling
4. **Documentation Updates**: All docs reflect current behavior
