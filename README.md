# Pasta - Clipboard to Keyboard

<p align="center">
  <img src="src-tauri/assets/logo.png" alt="Pasta Logo" width="256" height="256">
</p>

A lightweight system tray application that converts clipboard content into simulated keyboard input. Written in Rust using Tauri v2 for blazing fast performance and minimal resource usage.

## What is Pasta?

Pasta monitors your clipboard and automatically types out the content when you copy text. It's perfect for applications that don't support standard paste operations, like remote desktop sessions, VMs, or certain secure input fields.

## Features

- 🚀 **Lightweight & Fast**: ~20MB memory usage, <500ms startup time
- 🎯 **Simple & Focused**: Does one thing exceptionally well
- 🎨 **Native Look**: Follows system theme (light/dark mode)
- ⚡ **Adjustable Speed**: Three typing speeds (Slow, Normal, Fast)
- 🔒 **Privacy First**: No network access, no telemetry, no data collection
- 🖥️ **Cross-Platform**: Works on macOS, Windows, and Linux

## Installation

### Download Pre-built Binaries
Coming soon! For now, build from source.

### Build from Source

#### Prerequisites
- [Rust](https://rustup.rs/) 1.70+
- Platform-specific dependencies:
  - **macOS**: Xcode Command Line Tools
  - **Linux**: `sudo apt install libgtk-3-dev libwebkit2gtk-4.1-dev libayatana-appindicator3-dev`
  - **Windows**: Windows SDK

#### Build Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/pasta.git
cd pasta

# Install Tauri CLI
cargo install tauri-cli --version '^2.0.0' --locked

# Build the application
cargo tauri build

# The built application will be in:
# macOS: src-tauri/target/release/bundle/macos/Pasta.app
# Windows: src-tauri/target/release/bundle/msi/
# Linux: src-tauri/target/release/bundle/deb/
```

## Usage

1. **Launch Pasta** - It will appear in your system tray/menu bar
2. **Copy any text** - Pasta will detect the clipboard change
3. **Click where you want to type** - Position your cursor
4. **Watch Pasta type** - Your clipboard content is typed automatically

### Controls
- **Enable/Disable**: Toggle monitoring from the tray menu
- **Typing Speed**: Adjust speed in Settings or tray menu
- **Settings**: Access configuration window from tray menu
- **Quit**: Right-click tray icon and select Quit

## Configuration

Settings are automatically saved to:
- **macOS**: `~/Library/Application Support/com.pasta.rust/`
- **Linux**: `~/.config/pasta-rust/`
- **Windows**: `%APPDATA%\pasta-rust\`

## Development

```bash
# Run in development mode with hot reload
cargo tauri dev

# Run tests
cargo test

# Format code
cargo fmt

# Lint code
cargo clippy -- -D warnings
```

## Architecture

Pasta uses a multi-threaded architecture for optimal performance:
- **Main Thread**: UI and Tauri runtime
- **Clipboard Thread**: Monitors clipboard with 500ms polling
- **Keyboard Thread**: Handles text typing with chunking
- **Minimal Frontend**: Vanilla HTML/CSS/JS for settings

## Performance

| Metric | Value |
|--------|-------|
| Memory Usage | ~20-50 MB |
| Binary Size | ~10 MB |
| Startup Time | <500ms |
| CPU Usage (idle) | <0.1% |

## Privacy & Security

- **No Network Access**: Pasta works entirely offline
- **No Data Collection**: Your clipboard data never leaves your device
- **Open Source**: Audit the code yourself
- **Minimal Permissions**: Only clipboard read and keyboard emulation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure cross-platform compatibility
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Built with:
- [Tauri](https://tauri.app/) - Framework for building native apps
- [Arboard](https://github.com/1Password/arboard) - Cross-platform clipboard
- [Enigo](https://github.com/enigo-rs/enigo) - Cross-platform input simulation