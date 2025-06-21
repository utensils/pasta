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
cargo test config::

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
│   │   ├── config.rs         # TOML config persistence
│   │   ├── tray.rs           # System tray menu
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
- **Simple State Management**: Single AppState with keyboard emulator
- **System Tray Interface**: All interaction through tray menu
- **Cross-platform**: Works on macOS, Linux, and Windows
- **Zero Network Access**: No external communication, telemetry, or updates

### Key Architectural Components

1. **AppState** (lib.rs)
   - Simple state container with only keyboard emulator
   - Wrapped in `Arc` for thread-safe sharing
   - Exposes single Tauri IPC command: `paste_clipboard`
   - Business logic extracted to app_logic module for better testability

2. **Clipboard Access** (clipboard.rs)
   - Simple synchronous function to get current clipboard content
   - Uses `arboard` crate for cross-platform clipboard access
   - Returns `Option<String>` for text content
   - No monitoring or polling - only reads on demand

3. **KeyboardEmulator** (keyboard.rs)
   - Runs in separate thread to avoid blocking UI
   - Chunks text into 200-character segments
   - Configurable delays: Slow (50ms), Normal (25ms), Fast (10ms)
   - 100ms pause between chunks for system stability
   - Special character handling for newlines and tabs
   - Uses `enigo` crate for keyboard emulation

4. **ConfigManager** (config.rs)
   - Platform-specific config locations using `dirs` crate
   - Auto-saves on every change
   - Simple TOML format with `typing_speed` and `left_click_paste`
   - Default configuration: `typing_speed = "normal"`, `left_click_paste = false`
   - Handles migration from old config format

5. **TrayManager** (tray.rs)
   - Creates system tray icon with menu
   - Menu items:
     - Paste - triggers clipboard typing
     - Typing Speed submenu (Slow/Normal/Fast)
     - Left Click Pastes - toggle left-click behavior
     - Quit
   - Handles all user interaction
   - Works around Tauri v2 initialization bug with 100ms delay

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
- No settings window implemented
- All configuration through tray menu
- Future: Could add settings window if needed

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
- Each character typed individually with configurable delay
- Runs in separate thread to avoid blocking UI

### Configuration Persistence
- Stored in platform-standard locations:
  - macOS: `~/Library/Application Support/com.pasta.app/config.toml`
  - Linux: `~/.config/pasta/config.toml`  
  - Windows: `%APPDATA%\pasta\config.toml`
- Config fields:
  - `typing_speed`: "slow" | "normal" | "fast"
  - `left_click_paste`: boolean
- Auto-saves on change
- Handles migration from old format

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
- Unit tests for all modules (284 tests total, 31 ignored)
- Integration tests for cross-module functionality
- MockKeyboardEmulator for safe testing without typing on the system
- Tests marked with `#[ignore]` that would create real keyboard emulators
- Tests cover config persistence, keyboard emulation, tray menu behavior
- Run with `cargo test` for normal tests
- Run with `cargo test -- --ignored` to run tests that create real keyboard emulators
- Run with `cargo test -- --test-threads=1` to avoid segfaults on parallel execution
- Coverage reports with `cargo tarpaulin` or `./coverage.sh`
- CI skips certain tests that require display connection (clipboard, keyboard tests)
- Flaky timing tests are ignored in CI due to performance variability

### Current Limitations
- Text-only clipboard support (no images, files, etc.)
- No clipboard monitoring or history
- No global hotkeys
- No settings window (configuration via tray menu only)
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
   - Tests on Ubuntu, Windows, and macOS
   - Runs clippy and rustfmt checks
   - Generates code coverage reports
   - Uploads coverage to Codecov

2. **build.yml** - Build artifacts
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
- Coverage reports exclude certain files that can't be tested in CI