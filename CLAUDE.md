# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an experimental Rust/Tauri implementation of Pasta, demonstrating a minimal viable product with significantly better performance characteristics than the Python version. Located in the `rust-refactor` git worktree, this implementation focuses exclusively on core clipboard monitoring and keyboard typing functionality.

## Common Development Commands

### Prerequisites Setup
```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Tauri CLI v2
cargo install tauri-cli --version '^2.0.0' --locked

# Platform-specific dependencies
# Linux: sudo apt install libgtk-3-dev libwebkit2gtk-4.1-dev libayatana-appindicator3-dev
# macOS: Ensure Xcode Command Line Tools installed
# Windows: Ensure Windows SDK installed
```

### Development Workflow
```bash
# Run in development mode with hot reload
cargo tauri dev

# Run with debug logging
RUST_LOG=debug cargo tauri dev

# Build for production
cargo tauri build

# Format code
cargo fmt

# Run linter
cargo clippy

# Clean build artifacts
cargo clean

# Test a specific module (if tests were implemented)
cargo test clipboard -- --nocapture
```

## High-Level Architecture

### Core Design Principles
- **Minimal MVP**: Only clipboard monitoring and keyboard typing - no history, encryption, or advanced features
- **Multi-threaded**: Separate threads for clipboard monitoring, keyboard operations, and UI
- **Channel-based Communication**: Tokio MPSC channels for thread communication
- **Polling-based Monitoring**: 500ms clipboard polling interval (not event-based)
- **Zero Network Access**: No external communication, telemetry, or updates

### Project Structure
```
src-tauri/
├── src/
│   ├── main.rs          # Entry point, initializes Tauri
│   ├── lib.rs           # Core app orchestration, state management
│   ├── clipboard.rs     # ClipboardMonitor implementation
│   ├── keyboard.rs      # KeyboardEmulator with chunking logic
│   ├── config.rs        # TOML-based settings persistence
│   └── tray.rs          # System tray menu builder
├── assets/              # Runtime tray icons (template versions)
└── icons/               # Application bundle icons
```

### Key Architectural Components

1. **AppState** (lib.rs)
   - Central state container wrapped in `Arc` for thread-safe sharing
   - Manages clipboard monitor, keyboard emulator, and config manager
   - Coordinates component lifecycle

2. **ClipboardMonitor** (clipboard.rs)
   - Runs in dedicated thread with its own Tokio runtime
   - Uses content hashing to detect changes (DefaultHasher)
   - Sends clipboard content through MPSC channel
   - Respects enabled/disabled state dynamically

3. **KeyboardEmulator** (keyboard.rs)
   - Runs in separate thread to avoid blocking
   - Chunks text into 200-character segments
   - Configurable delays: Slow (50ms), Normal (25ms), Fast (10ms)
   - 100ms pause between chunks for system stability

4. **ConfigManager** (config.rs)
   - Platform-specific config locations using `dirs` crate
   - Auto-saves on every change
   - Graceful defaults if config missing
   - Simple TOML format with just `enabled` and `typing_speed`

### Threading Model
```
Main Thread (Tauri/UI)
    ├── Clipboard Monitor Thread (dedicated Tokio runtime)
    │   └── 500ms polling loop
    ├── Keyboard Thread (receives from clipboard via channel)
    │   └── Text chunking and typing
    └── Settings Window (on-demand)
```

### Frontend Architecture
- Vanilla HTML/CSS/JavaScript (no framework)
- Single `index.html` settings window
- Tauri IPC commands: `get_config`, `set_enabled`, `set_typing_speed`
- Visual save confirmation with 2-second fade

## Implementation Notes

### Clipboard Monitoring Strategy
- Polling-based (not event-based) for cross-platform compatibility
- 500ms interval balances responsiveness vs CPU usage
- Empty clipboard content ignored
- Content comparison via hash to detect changes

### Keyboard Typing Implementation
- Uses `enigo` crate for cross-platform keyboard emulation
- Special handling for newlines (`\n`) and tabs (`\t`)
- Text chunking prevents system overload with large pastes
- Each character typed individually with configurable delay

### Configuration Persistence
- Stored in platform-standard locations:
  - macOS: `~/Library/Application Support/com.pasta.rust/config.toml`
  - Linux: `~/.config/pasta-rust/config.toml`  
  - Windows: `%APPDATA%\pasta-rust\config.toml`
- Minimal config with just two fields: `enabled` and `typing_speed`

### Tauri-specific Considerations
- System tray icons use `iconAsTemplate` for proper macOS dark mode support
- No CSP restrictions for simpler development
- Frontend served from `src/` directory (not built/bundled)
- Bundle includes platform-specific icon formats

## Performance Characteristics
- Memory usage: 20-50MB (vs Python's 100-200MB)
- Binary size: ~10MB (vs Python's 50-100MB)
- Startup time: <500ms (vs Python's 2-3 seconds)
- Idle CPU: <0.1% (vs Python's 1-2%)

## Development Guidelines

### When Adding Features
1. Maintain minimal approach - question if feature is truly core
2. Ensure thread safety with Arc/Mutex when sharing state
3. Use channels for cross-thread communication
4. Keep frontend simple - no frameworks or complex build steps
5. Test on all platforms before committing

### Current Limitations
- Text-only clipboard support (no images, files, etc.)
- No clipboard history storage
- No hotkey support (would require additional permissions)
- No emergency stop mechanism
- No security features or sensitive data detection
- No rate limiting or abuse prevention

### Git Worktree Notes
This code lives in a git worktree at `./trees/rust-refactor`. When working here:
- The actual branch is `rust-refactor` (not main)
- Commits go to the `rust-refactor` branch
- Use `git worktree list` from main repo to see all worktrees
- Changes are isolated from the main Python implementation