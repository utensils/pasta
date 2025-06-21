# Pasta

[![codecov](https://codecov.io/gh/utensils/pasta/graph/badge.svg)](https://codecov.io/gh/utensils/pasta)
[![CI](https://github.com/utensils/pasta/actions/workflows/rust.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/rust.yml)

<p align="center">
  <img src="src-tauri/assets/logo.png" alt="Pasta Logo" width="256" height="256">
</p>

A minimal system tray application that types your clipboard content. Perfect for situations where standard paste doesn't work.

## Installation

### Download Pre-built Binaries

Download the latest release from the [Releases page](https://github.com/utensils/pasta/releases).

#### macOS Users - Important Note

The macOS builds are currently unsigned. To run Pasta on macOS:

**Option 1 - Using Finder:**
1. Download the .dmg file
2. Open the .dmg and drag Pasta to Applications
3. Right-click (or Control-click) on Pasta.app
4. Select "Open" from the context menu
5. Click "Open" in the dialog that appears

**Option 2 - Using Terminal:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/Pasta.app
```

**Option 3 - Allow in System Settings:**
1. Try to open Pasta normally
2. Go to System Settings > Privacy & Security
3. Look for "Pasta was blocked" message
4. Click "Open Anyway"

### Build from Source

```bash
# Prerequisites
# - Rust 1.70+
# - Platform-specific dependencies (see Tauri docs)

# Clone and build
git clone https://github.com/utensils/pasta.git
cd pasta
cargo install tauri-cli --version '^2.0.0' --locked
cargo tauri build
```

## Usage

1. Launch Pasta - appears in system tray
2. Copy text normally (Ctrl+C/Cmd+C)
3. Click "Paste" in tray menu to type it out

Adjust typing speed and left-click behavior from the tray menu.

## Configuration

Pasta stores its configuration file in the following locations:

- **macOS**: `~/Library/Application Support/com.pasta.app/config.toml`
- **Linux**: `~/.config/pasta/config.toml`
- **Windows**: `%APPDATA%\pasta\config.toml`

The configuration file is automatically created on first run with defaults (normal typing speed, left-click shows menu) and saves your preferences.

## Development

```bash
# Run in development mode
cargo tauri dev

# Run tests
cargo test --lib

# Using Nix (recommended)
nix develop
menu  # Shows all available commands
```

## License

MIT License - see [LICENSE](LICENSE) file for details.