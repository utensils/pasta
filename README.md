# Pasta - Clipboard to Keyboard

[![codecov](https://codecov.io/gh/utensils/pasta/graph/badge.svg)](https://codecov.io/gh/utensils/pasta)
[![CI](https://github.com/utensils/pasta/actions/workflows/rust.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/rust.yml)

<p align="center">
  <img src="src-tauri/assets/logo.png" alt="Pasta Logo" width="256" height="256">
</p>

A lightweight system tray application that converts clipboard content into simulated keyboard input. Written in Rust using Tauri v2 for blazing fast performance and minimal resource usage.

## What is Pasta?

Pasta allows you to paste clipboard content by simulating keyboard typing. When you click "Paste" from the system tray menu, it types out whatever text is currently in your clipboard. It's perfect for applications that don't support standard paste operations, like remote desktop sessions, VMs, or certain secure input fields.

## Features

- 🚀 **Lightweight & Fast**: ~20MB memory usage, <500ms startup time
- 🎯 **Simple & Focused**: Does one thing exceptionally well
- 🎨 **Native Look**: Follows system theme (light/dark mode)
- ⚡ **Adjustable Speed**: Three typing speeds (Slow, Normal, Fast)
- 🖱️ **Configurable Tray Icon**: Choose between left-click paste or menu
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
2. **Copy any text** - Use your normal copy methods (Ctrl+C, Cmd+C, etc.)
3. **Click where you want to type** - Position your cursor in the target application
4. **Click "Paste" in tray menu** - Pasta will type out your clipboard content

### Controls
- **Paste**: Click "Paste" in tray menu to type clipboard content
- **Typing Speed**: Adjust speed in Settings or tray menu  
- **Left-Click Behavior**: Configure in Settings to either paste directly or show menu
- **Settings**: Access configuration window from tray menu
- **Quit**: Right-click tray icon and select Quit

## Configuration

Settings are automatically saved to:
- **macOS**: `~/Library/Application Support/com.pasta.app/`
- **Linux**: `~/.config/pasta/`
- **Windows**: `%APPDATA%\pasta\`

## Development

### Quick Start

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

### Using Nix (Recommended)

This project includes a Nix flake with a powerful devshell for reproducible development environments. If you have [Nix](https://nixos.org/) installed with flakes enabled:

```bash
# Enter development shell with all dependencies
nix develop

# Show the interactive development menu
menu

# Or run commands directly:
nix develop -c dev          # Run in development mode
nix develop -c run-tests    # Run tests
nix develop -c build        # Build for production
```

#### Available Commands

The Nix devshell provides convenient commands for all common tasks:

**Development**
- `dev` - Run in development mode with hot reload
- `dev-debug` - Run with debug logging enabled
- `run` - Build and run the application directly
- `watch` - Watch for changes and rebuild

**Building**
- `build` - Build for production
- `build-debug` - Build in debug mode (faster compile, larger binary)

**Testing**
- `run-tests` - Run all tests
- `test-lib` - Run library tests (excludes clipboard tests)
- `test-watch` - Run tests in watch mode
- `coverage` - Generate test coverage report
- `coverage-html` - Generate and open HTML coverage report

**Code Quality**
- `fmt` - Format code with rustfmt
- `fmt-check` - Check code formatting
- `lint` - Run clippy linter
- `lint-fix` - Run clippy and attempt to fix issues
- `check` - Run format check and linter

**Maintenance**
- `clean` - Clean build artifacts
- `clean-all` - Clean all artifacts including coverage
- `update` - Update dependencies
- `outdated` - Check for outdated dependencies
- `audit` - Audit dependencies for security vulnerabilities

**Other**
- `expand` - Expand macros for debugging
- `install-hooks` - Install git pre-commit hooks

All commands are accessible through the interactive `menu` or by running them directly:

```bash
# Using the menu (recommended)
nix develop
menu

# Or run commands directly
nix develop -c test-lib
nix develop -c coverage
```

The Nix flake provides:
- All required dependencies and build tools
- Rust toolchain with cross-compilation targets
- Platform-specific frameworks and libraries
- Development utilities (cargo-watch, rust-analyzer, etc.)
- Pre-configured environment variables
- Automatic directory setup

Alternative development shells:
```bash
nix develop .#ci      # Minimal CI environment
nix develop .#minimal # Basic Rust toolchain only
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure cross-platform compatibility
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [Tauri](https://tauri.app/) - Framework for building native apps
- [Arboard](https://github.com/1Password/arboard) - Cross-platform clipboard
- [Enigo](https://github.com/enigo-rs/enigo) - Cross-platform input simulation