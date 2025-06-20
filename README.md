# Pasta

[![codecov](https://codecov.io/gh/utensils/pasta/graph/badge.svg)](https://codecov.io/gh/utensils/pasta)
[![CI](https://github.com/utensils/pasta/actions/workflows/rust.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/rust.yml)

<p align="center">
  <img src="src-tauri/assets/logo.png" alt="Pasta Logo" width="256" height="256">
</p>

A minimal system tray application that types your clipboard content. Perfect for situations where standard paste doesn't work.

## Installation

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

## Development

```bash
# Run in development mode
cargo tauri dev

# Run tests
cargo test

# Using Nix (recommended)
nix develop
menu  # Shows all available commands
```

## License

MIT License - see [LICENSE](LICENSE) file for details.