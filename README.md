# Pasta Rust - Experimental Tauri Implementation

This is an experimental Rust/Tauri implementation of Pasta, a cross-platform system tray application that converts clipboard content into simulated keyboard input.

## Overview

This branch contains a minimal MVP implementation of Pasta written in Rust using the Tauri v2 framework. It focuses on core functionality only - clipboard monitoring and keyboard typing simulation - without the advanced features of the Python version.

## Features

### Implemented ✅
- **System Tray Icon**: Native system tray with custom Pasta branding
- **Clipboard Monitoring**: Background monitoring with 500ms polling interval
- **Keyboard Typing**: Simulates keyboard input for clipboard content
- **Typing Speed Control**: Three speed settings (Slow, Normal, Fast)
- **Enable/Disable Toggle**: Turn monitoring on/off from tray menu
- **Settings Window**: Simple GUI for configuration
- **Configuration Persistence**: Settings saved to TOML file
- **Cross-platform Support**: Works on Windows, macOS, and Linux

### Not Implemented ❌
- Clipboard history storage
- Encryption of sensitive data
- Hotkey support
- Snippet management
- Advanced paste modes (typing vs clipboard)
- Rate limiting
- Security features (password detection, etc.)
- Emergency stop functionality
- Multiple language support

## Technology Stack

- **Language**: Rust
- **Framework**: Tauri v2
- **System Tray**: tauri-plugin-tray
- **Clipboard**: arboard (cross-platform clipboard library)
- **Keyboard**: enigo (cross-platform keyboard/mouse automation)
- **Configuration**: TOML via serde
- **Async Runtime**: Tokio

## Building and Running

### Prerequisites
- Rust 1.70+ (install from https://rustup.rs)
- Node.js 16+ (for frontend build tools)
- Platform-specific dependencies:
  - **Linux**: `libgtk-3-dev`, `libwebkit2gtk-4.1-dev`, `libayatana-appindicator3-dev`
  - **macOS**: Xcode Command Line Tools
  - **Windows**: Windows SDK

### Development
```bash
# Install Tauri CLI
cargo install tauri-cli --version '^2.0.0' --locked

# Install frontend dependencies
npm install

# Run in development mode
cargo tauri dev

# The app will start with hot-reload enabled
```

### Building for Production
```bash
# Build optimized binary
cargo tauri build

# Output locations:
# macOS: src-tauri/target/release/bundle/macos/Pasta.app
# Windows: src-tauri/target/release/bundle/msi/Pasta_0.1.0_x64.msi
# Linux: src-tauri/target/release/bundle/deb/pasta-rust_0.1.0_amd64.deb
```

## Architecture

### Project Structure
```
├── src/                    # Frontend (HTML/CSS/JS)
│   ├── index.html         # Settings window HTML
│   ├── main.js           # Settings window logic
│   └── styles.css        # Settings window styles
├── src-tauri/            # Rust backend
│   ├── src/
│   │   ├── main.rs       # Entry point
│   │   ├── lib.rs        # Main application logic
│   │   ├── clipboard.rs  # Clipboard monitoring
│   │   ├── keyboard.rs   # Keyboard emulation
│   │   ├── config.rs     # Configuration management
│   │   └── tray.rs       # System tray implementation
│   ├── icons/            # Application icons
│   ├── assets/           # Runtime assets (tray icons)
│   └── Cargo.toml        # Rust dependencies
```

### Key Components

1. **ClipboardMonitor**: Polls system clipboard every 500ms for changes
2. **KeyboardEmulator**: Types text using enigo with configurable speed
3. **ConfigManager**: Handles TOML config file persistence
4. **TrayManager**: Creates and manages system tray menu

### Configuration

Settings are stored in a TOML file at:
- **macOS**: `~/Library/Application Support/com.pasta.rust/config.toml`
- **Linux**: `~/.config/pasta-rust/config.toml`
- **Windows**: `%APPDATA%\pasta-rust\config.toml`

Example config:
```toml
enabled = true
typing_speed = "Normal"
```

## Performance Comparison

| Metric | Python Version | Rust Version |
|--------|---------------|--------------|
| Memory Usage | 100-200 MB | 20-50 MB |
| Binary Size | 50-100 MB | ~10 MB |
| Startup Time | 2-3 seconds | < 500ms |
| CPU Usage (idle) | 1-2% | < 0.1% |

## Development Status

This is an **experimental branch** demonstrating the feasibility of a Rust implementation. It is not feature-complete and is intended as a proof-of-concept for potential future development.

### Why Rust/Tauri?

- **Performance**: Significantly lower memory and CPU usage
- **Binary Size**: Much smaller distributable size
- **Native Feel**: Better OS integration through Tauri
- **Security**: Memory safety guarantees from Rust
- **Modern Stack**: Leverages latest web technologies with native performance

### Limitations

- Minimal feature set compared to Python version
- Less mature ecosystem for some functionality
- Requires more low-level implementation work
- Limited clipboard format support (text only)

## Contributing

This branch is experimental. If you're interested in helping develop the Rust version:

1. Check the main Python implementation for feature parity goals
2. Focus on core functionality first
3. Ensure cross-platform compatibility
4. Write tests for new features
5. Keep the codebase minimal and efficient

## License

Same as the main Pasta project - see the root LICENSE file.