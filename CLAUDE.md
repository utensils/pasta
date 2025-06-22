# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pasta is a minimal system tray application that types your clipboard content, built with Rust and Tauri v2. It provides a simple solution for situations where standard paste functionality doesn't work (like in certain remote desktop applications or web-based terminals).

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

# Run tests including ignored ones (tests that create real keyboard emulators)
cargo test -- --ignored

# Run all tests including ignored ones
cargo test -- --include-ignored

# Run specific test module
cargo test keyboard::

# Run tests with output
cargo test -- --nocapture

# Run tests with single thread to avoid segfaults
cargo test -- --test-threads=1

# Run only library tests
cargo test --lib

# Run tests in release mode for better performance
cargo test --release

# Run with specific logging levels
RUST_LOG=pasta=debug cargo tauri dev

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
cargo tauri build --target aarch64-apple-darwin

# Install npm dependencies (required for Tauri builds)
npm install

# Trigger release workflow manually
gh workflow run release.yml -f tag_name=v0.1.0-dev
```

## Project Structure

```
pasta/
├── src/                        # Frontend (minimal HTML/CSS/JS)
│   ├── index.html             # Settings window UI (currently unused)
│   └── assets/                # Frontend assets
│       ├── javascript.svg
│       └── tauri.svg
├── src-tauri/                 # Rust/Tauri backend
│   ├── src/
│   │   ├── main.rs           # Entry point
│   │   ├── lib.rs            # App orchestration, state management
│   │   ├── app_logic.rs      # Business logic for paste and menu operations
│   │   ├── clipboard.rs      # Clipboard content retrieval
│   │   ├── keyboard.rs       # Keyboard emulation with text chunking
│   │   ├── tray.rs           # System tray menu
│   │   ├── hotkey.rs         # Global hotkey management (double-Escape)
│   │   ├── helpers.rs        # Helper functions for logging and utilities
│   │   ├── mock_keyboard.rs  # Mock keyboard emulator for testing
│   │   ├── theme.rs          # Theme utilities (currently unused)
│   │   └── *_tests.rs        # Various test modules (unit and integration tests)
│   ├── assets/               # Tray icons (multiple sizes)
│   ├── icons/                # App bundle icons
│   ├── capabilities/         # Tauri permissions
│   ├── tests/                # Integration tests
│   ├── Cargo.toml           # Rust dependencies
│   └── tauri.conf.json      # Tauri configuration
├── .github/
│   └── workflows/
│       ├── rust.yml          # CI for tests and coverage
│       ├── build.yml         # Build artifacts for all platforms
│       └── release.yml       # Create GitHub releases with artifacts
├── flake.nix                 # Nix development environment
├── package.json              # Minimal npm config for Tauri builds
├── README.md                 # User documentation
└── CLAUDE.md                 # This file

## High-Level Architecture

### Core Design Principles
- **Minimal Functionality**: Only types clipboard content - no monitoring, history, or advanced features
- **Stateless Design**: No configuration persistence - always uses default Normal typing speed
- **Simple State Management**: Single AppState with keyboard emulator and cancellation flag
- **System Tray Interface**: All interaction through tray menu
- **Cross-platform**: Works on macOS, Linux, and Windows
- **Zero Network Access**: No external communication, telemetry, or updates
- **Emergency Stop**: Double-Escape hotkey to instantly cancel typing operations

### Key Architectural Components

1. **AppState** (lib.rs)
   - State container with keyboard emulator and cancellation flag
   - Wrapped in `Arc` for thread-safe sharing
   - Exposes Tauri IPC commands: `paste_clipboard` and `cancel_typing`
   - Includes methods for cancellation: `cancel_typing()`, `reset_cancellation()`, `is_cancelled()`
   - Business logic extracted to app_logic module for better testability

2. **Clipboard Access** (clipboard.rs)
   - Simple synchronous function to get current clipboard content
   - Uses `arboard` crate for cross-platform clipboard access
   - Returns `Option<String>` for text content
   - No monitoring or polling - only reads on demand

3. **KeyboardEmulator** (keyboard.rs)
   - Runs in separate thread to avoid blocking UI
   - Chunks text into 200-character segments
   - Fixed Normal typing speed (25ms delay between characters)
   - 100ms pause between chunks for system stability
   - Special character handling for newlines and tabs
   - Uses `enigo` crate for keyboard emulation
   - Supports cancellation via atomic flag checked during typing
   - Checks cancellation flag at chunk boundaries and every 10 characters

4. **TrayManager** (tray.rs)
   - Creates system tray icon with menu
   - Menu items:
     - Paste - triggers clipboard typing
     - Cancel Typing (Esc Esc) - cancels ongoing typing operation
     - Quit
   - Handles all user interaction
   - Works around Tauri v2 initialization bug with 100ms delay

5. **HotkeyManager** (hotkey.rs)
   - Manages global keyboard shortcuts
   - Uses `tauri-plugin-global-shortcut` for cross-platform hotkey support
   - Implements double-Escape detection with 500ms time window
   - Triggers cancellation when double-Escape is pressed
   - Alternative: Supports Ctrl+Shift+Escape for simpler implementation

6. **Helper Functions** (helpers.rs)
   - Extracted helper functions for better testability
   - Logging formatters for consistent messages
   - Platform-specific utilities (e.g., macOS activation policy)
   - Startup delay configuration

### Threading Model
```
Main Thread (Tauri/UI)
    └── Keyboard Thread (spawned on paste action)
        └── Text chunking and typing
```

### Frontend Architecture
- Currently minimal - just a placeholder HTML file
- No settings window needed (stateless design)
- All interaction through tray menu

## Implementation Notes

### Clipboard Access
- On-demand reading only (no monitoring or polling)
- Uses `arboard` crate for cross-platform support
- Returns `None` for empty clipboard or non-text content
- Error handling for clipboard access failures

### Keyboard Typing Implementation
- Uses `enigo` crate for cross-platform keyboard emulation
- Special handling for newlines (`\n`) and tabs (`\t`)
- Text chunking (200 chars) prevents system overload with large pastes
- Each character typed individually with fixed 25ms delay (Normal speed)
- Runs in separate thread to avoid blocking UI
- Emergency stop: Press Escape twice within 500ms to cancel typing
- Cancellation checked at chunk boundaries and every 10 characters
- Thread-safe cancellation using atomic boolean flag

### Stateless Design
- No configuration persistence
- Always uses Normal typing speed (25ms delay)
- Simple and predictable behavior

### Tauri-specific Considerations
- Uses Tauri v2 with improved performance
- System tray only (no main window)
- 100ms delay on startup to work around Tauri menu initialization bug
- Icons in multiple sizes for different platforms
- Minimal frontend - just placeholder HTML

## Performance Characteristics
- Memory usage: ~20-30MB idle
- Binary size: ~10MB
- Startup time: <500ms
- Idle CPU: 0% (no background polling)

## Platform-Specific Notes

### macOS
- Requires accessibility permissions for keyboard emulation
- Template icons for proper dark mode support
- Unsigned builds require user approval (right-click > Open or xattr -d com.apple.quarantine)
- Code signing needed for distribution without security warnings
- Dock icon hidden when no windows open (menu bar app behavior)
- Window close button hides window instead of quitting app
- Uses `ActivationPolicy::Accessory` for background operation
- Hardened runtime disabled in config for unsigned builds

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
The project has comprehensive test coverage:
- Unit tests for all modules (300+ tests total, ~40 ignored)
- Integration tests for cross-module functionality
- MockKeyboardEmulator for safe testing without typing on the system
- Tests marked with `#[ignore]` that would create real keyboard emulators
- Tests that create GUI components also marked with `#[cfg(not(tarpaulin))]` to exclude from coverage
- Tests cover keyboard emulation, tray menu behavior, cancellation logic
- Run with `cargo test` for normal tests
- Run with `cargo test -- --ignored` to run tests that create real keyboard emulators
- Run with `cargo test -- --test-threads=1` to avoid segfaults on parallel execution
- Coverage reports with `cargo tarpaulin`
- CI skips certain tests that require display connection (clipboard, keyboard tests)
- Flaky timing tests are ignored in CI due to performance variability

#### Coverage Configuration
Code coverage excludes the following files as they contain mostly Tauri boilerplate or GUI code:
- `*/lib.rs` - Tauri app initialization
- `*/tray.rs` - System tray GUI components
- `*/window.rs` - Window management code
- `*/clipboard.rs` - Requires display connection
- All test files (`*_tests.rs`)

This focuses coverage metrics on actual business logic rather than framework code.

### Current Limitations
- Text-only clipboard support (no images, files, etc.)
- No clipboard monitoring or history
- No global hotkeys (except for emergency stop)
- No settings or configuration
- No automatic update mechanism

### Debugging Tips
- Use `RUST_LOG=debug` for verbose logging
- Check platform-specific console output
- Verify permissions (especially on macOS)
- Monitor thread activity with system tools
- Use `cargo tauri inspect` to check bundle configuration

## CI/CD and Release Process

### GitHub Actions Workflows

1. **rust.yml** - Main CI pipeline
   - Runs on push/PR to main branch
   - Only triggers when code files change (not on documentation updates)
   - Tests on Ubuntu, Windows, and macOS
   - Runs clippy and rustfmt checks
   - Generates code coverage reports
   - Uploads coverage to Codecov
   - Coverage excludes GUI/framework code to focus on business logic

2. **build.yml** - Build artifacts
   - Only triggers on release tags (v*) or manual dispatch
   - Builds release artifacts for all platforms
   - Uploads artifacts to GitHub Actions
   - Useful for testing builds without creating releases

3. **release.yml** - Release pipeline
   - Triggers on version tags (v*) or manual dispatch
   - Builds for all platforms: Linux x86_64, Windows x86_64, macOS x86_64 & aarch64
   - Creates draft GitHub releases with all artifacts
   - Uses tauri-action for automated builds

### Release Artifacts

**Linux:**
- `.AppImage` - Universal package that runs on most distributions
- `.deb` - Debian/Ubuntu package
- `.rpm` - Fedora/RHEL package

**Windows:**
- `.exe` - NSIS installer (recommended)
- `.msi` - MSI installer

**macOS:**
- `.dmg` - Disk image installer (separate builds for Intel and Apple Silicon)
- `.app.tar.gz` - Compressed app bundle

### Creating a Release

1. Update version in `src-tauri/tauri.conf.json`
2. Commit changes
3. Create and push a tag:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```
4. GitHub Actions will automatically build and create a draft release
5. Edit release notes and publish when ready

### Known Issues

- macOS builds are unsigned and require user approval to run
- Some tests are skipped in CI due to requiring display/clipboard access
- Coverage reports exclude GUI/framework files to focus on business logic (~70% coverage target)
- Tests that create keyboard emulators must be marked with both `#[ignore]` and `#[cfg(not(tarpaulin))]`