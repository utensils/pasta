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
cargo clippy -- -D warnings

# Clean build artifacts
cargo clean

# Run tests
cargo test

# Run specific test module
cargo test config::

# Run tests with output
cargo test -- --nocapture

# Run tests excluding clipboard tests (which may segfault on some systems)
cargo test --lib -- config:: window::

# Run tests in release mode for better performance
cargo test --release

# Run with specific logging levels
RUST_LOG=pasta_rust=debug cargo tauri dev

# Coverage reporting
cargo tarpaulin --out Html --exclude-files "*/clipboard.rs" -- --lib

# Generate coverage report and open in browser
make coverage-open

# Generate coverage in multiple formats (XML, LCOV, HTML)
make coverage-ci

# Clean coverage artifacts
make clean-coverage

# Run coverage with the shell script (recommended)
./coverage.sh

# Build for specific platform
cargo tauri build --target x86_64-apple-darwin
cargo tauri build --target x86_64-pc-windows-msvc
cargo tauri build --target x86_64-unknown-linux-gnu
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
│   ├── tray.rs          # System tray menu builder
│   ├── window.rs        # Window management and behavior
│   └── theme.rs         # Theme detection and color management
├── assets/              # Runtime tray icons (template versions)
├── icons/               # Application bundle icons
└── capabilities/        # Tauri permission configurations

src/                     # Frontend code (vanilla HTML/CSS/JS)
└── index.html          # Settings window UI
```

### Key Architectural Components

1. **AppState** (lib.rs)
   - Central state container wrapped in `Arc` for thread-safe sharing
   - Manages clipboard monitor, keyboard emulator, and config manager
   - Coordinates component lifecycle
   - Exposes Tauri IPC commands: `get_config`, `set_enabled`, `set_typing_speed`

2. **ClipboardMonitor** (clipboard.rs)
   - Runs in dedicated thread with its own Tokio runtime
   - Uses content hashing to detect changes (DefaultHasher)
   - Sends clipboard content through MPSC channel
   - Respects enabled/disabled state dynamically
   - Gracefully handles clipboard access errors

3. **KeyboardEmulator** (keyboard.rs)
   - Runs in separate thread to avoid blocking
   - Chunks text into 200-character segments
   - Configurable delays: Slow (50ms), Normal (25ms), Fast (10ms)
   - 100ms pause between chunks for system stability
   - Special character handling for newlines and tabs

4. **ConfigManager** (config.rs)
   - Platform-specific config locations using `dirs` crate
   - Auto-saves on every change
   - Graceful defaults if config missing
   - Simple TOML format with just `enabled` and `typing_speed`

5. **WindowManager** (window.rs)
   - Handles settings window lifecycle
   - Prevents app quit on window close (hides instead)
   - Manages dock icon visibility on macOS
   - Window starts hidden to prevent flash

6. **Theme System** (theme.rs + CSS)
   - Automatic light/dark mode detection via CSS media queries
   - System-native color palette (matches macOS design)
   - CSS variables for consistent theming
   - Smooth animations for user feedback

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
- Tauri IPC commands: `get_config`, `save_config`
- Visual save confirmation with floating indicator
- Accessible form controls with proper labels
- Automatic light/dark theme support
- System-native styling (matches macOS UI conventions)

## Implementation Notes

### Clipboard Monitoring Strategy
- Polling-based (not event-based) for cross-platform compatibility
- 500ms interval balances responsiveness vs CPU usage
- Empty clipboard content ignored
- Content comparison via hash to detect changes
- Error handling for clipboard access failures

### Keyboard Typing Implementation
- Uses `enigo` crate for cross-platform keyboard emulation
- Special handling for newlines (`\n`) and tabs (`\t`)
- Text chunking prevents system overload with large pastes
- Each character typed individually with configurable delay
- Thread-safe operation with proper synchronization

### Configuration Persistence
- Stored in platform-standard locations:
  - macOS: `~/Library/Application Support/com.pasta.rust/config.toml`
  - Linux: `~/.config/pasta-rust/config.toml`  
  - Windows: `%APPDATA%\pasta-rust\config.toml`
- Minimal config with just two fields: `enabled` and `typing_speed`
- Directory creation handled automatically

### Tauri-specific Considerations
- System tray icons use `iconAsTemplate` for proper macOS dark mode support
- No CSP restrictions for simpler development
- Frontend served from `src/` directory (not built/bundled)
- Bundle includes platform-specific icon formats
- Capabilities configured in `capabilities/default.json`

## Performance Characteristics
- Memory usage: 20-50MB (vs Python's 100-200MB)
- Binary size: ~10MB (vs Python's 50-100MB)
- Startup time: <500ms (vs Python's 2-3 seconds)
- Idle CPU: <0.1% (vs Python's 1-2%)

## Platform-Specific Notes

### macOS
- Requires accessibility permissions for keyboard emulation
- Template icons for proper dark mode support
- Code signing needed for distribution
- Dock icon hidden when no windows open (menu bar app behavior)
- Window close button hides window instead of quitting app
- Uses `ActivationPolicy::Accessory` for background operation

### Linux
- Requires X11 or Wayland support
- AppIndicator support for system tray
- May need additional permissions on some distributions

### Windows
- Works out of the box with standard permissions
- Native system tray support
- May trigger antivirus warnings (keyboard emulation)

## Development Guidelines

### When Adding Features
1. Maintain minimal approach - question if feature is truly core
2. Ensure thread safety with Arc/Mutex when sharing state
3. Use channels for cross-thread communication
4. Keep frontend simple - no frameworks or complex build steps
5. Test on all platforms before committing

### Testing Strategy
Currently, the project lacks formal tests. When implementing tests:
- Use `cargo test` for unit tests
- Focus on testing core logic (clipboard detection, config persistence)
- Mock external dependencies (clipboard, keyboard)
- Test thread synchronization and error handling

### Current Limitations
- Text-only clipboard support (no images, files, etc.)
- No clipboard history storage
- No hotkey support (would require additional permissions)
- No emergency stop mechanism
- No security features or sensitive data detection
- No rate limiting or abuse prevention
- No automatic update mechanism

### Git Worktree Notes
This code lives in a git worktree at `./trees/rust-refactor`. When working here:
- The actual branch is `rust-refactor` (not main)
- Commits go to the `rust-refactor` branch
- Use `git worktree list` from main repo to see all worktrees
- Changes are isolated from the main Python implementation

### Debugging Tips
- Use `RUST_LOG=debug` for verbose logging
- Check platform-specific console output
- Verify permissions (especially on macOS)
- Monitor thread activity with system tools
- Use `cargo tauri inspect` to check bundle configuration