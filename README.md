# Pasta

[![Rust CI](https://github.com/utensils/pasta/actions/workflows/rust.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/rust.yml)
[![Build](https://github.com/utensils/pasta/actions/workflows/build.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/utensils/pasta/graph/badge.svg)](https://codecov.io/gh/utensils/pasta)
[![License Check](https://github.com/utensils/pasta/actions/workflows/license-check.yml/badge.svg)](https://github.com/utensils/pasta/actions/workflows/license-check.yml)

<p align="center">
  <img src="src-tauri/assets/logo.png" alt="Pasta Logo" width="256" height="256">
</p>

A minimal system tray application that types your clipboard content. Perfect for situations where standard paste doesn't work.

## Installation

### Download Pre-built Binaries

Download the latest release from the [Releases page](https://github.com/utensils/pasta/releases).

#### GNOME Users - System Tray Support

GNOME removed native system tray support starting with version 3.26. To use Pasta on GNOME, you'll need to install an extension:

**Option 1: Install via package manager (recommended)**
```bash
# Ubuntu/Debian
sudo apt install gnome-shell-extension-appindicator

# Fedora
sudo dnf install gnome-shell-extension-appindicator

# Arch
sudo pacman -S gnome-shell-extension-appindicator
```

**Option 2: Install from GNOME Extensions website**
1. Visit [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/)
2. Click "Install" and follow the prompts
3. Enable the extension in GNOME Extensions or Tweaks

After installation, restart GNOME Shell (Alt+F2, type 'r', press Enter) or log out and back in.

### Run with Nix

If you have Nix installed, you can run Pasta directly without installing:

```bash
nix run github:utensils/pasta
```

#### macOS Users - Important Notes

**1. Accessibility Permissions Required**

Pasta requires accessibility permissions to simulate keyboard input:
1. Open **System Preferences → Security & Privacy → Privacy → Accessibility**
2. Click the lock icon to make changes (enter your password)
3. Add Pasta.app by clicking the "+" button or drag it into the list
4. Ensure the checkbox next to Pasta is checked

If Pasta doesn't type anything when you click "Paste", this is usually the issue.

**2. Unsigned Build Warning**

The macOS builds are currently unsigned. To run Pasta on macOS, you'll need to remove the quarantine attribute:

**Using Terminal (Recommended):**
```bash
# After installing Pasta.app to Applications folder
xattr -d com.apple.quarantine /Applications/Pasta.app
```

This command removes the quarantine flag that macOS adds to downloaded applications. You only need to run this once.

**Alternative Methods:**
- **Right-click Method**: Right-click on Pasta.app and select "Open" (may not work on all systems)
- **System Settings**: Check System Settings > Privacy & Security for "Open Anyway" option

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

### Cancelling Typing

To instantly stop typing:
- **Click the tray icon** during a paste operation, or
- Click "Cancel Typing" in the tray menu

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