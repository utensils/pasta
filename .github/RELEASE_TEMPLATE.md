# Release vX.X.X

## ✨ What's Changed
<!-- List major changes here -->

## 📦 Downloads

Download the appropriate installer for your platform:

### 🪟 Windows
- **Installer (Recommended)**: [Pasta_X.X.X_x64-setup.exe](https://github.com/utensils/pasta/releases/download/vX.X.X/Pasta_X.X.X_x64-setup.exe)
- **MSI Package**: [Pasta_X.X.X_x64_en-US.msi](https://github.com/utensils/pasta/releases/download/vX.X.X/Pasta_X.X.X_x64_en-US.msi)

> **Note**: May trigger antivirus warnings due to keyboard emulation. This is expected behavior.

### 🍎 macOS
- **Intel Macs**: [Pasta_X.X.X_x64.dmg](https://github.com/utensils/pasta/releases/download/vX.X.X/Pasta_X.X.X_x64.dmg)
- **Apple Silicon (M1/M2/M3)**: [Pasta_X.X.X_aarch64.dmg](https://github.com/utensils/pasta/releases/download/vX.X.X/Pasta_X.X.X_aarch64.dmg)

> **Important**: macOS builds are unsigned. You'll need to:
> 1. Right-click the app and select "Open" on first launch, or
> 2. Remove quarantine: `xattr -d com.apple.quarantine /Applications/Pasta.app`
> 
> The app requires accessibility permissions for keyboard emulation.

### 🐧 Linux
- **AppImage (Universal)**: [pasta-tray_X.X.X_amd64.AppImage](https://github.com/utensils/pasta/releases/download/vX.X.X/pasta-tray_X.X.X_amd64.AppImage)
- **Debian/Ubuntu**: [pasta-tray_X.X.X_amd64.deb](https://github.com/utensils/pasta/releases/download/vX.X.X/pasta-tray_X.X.X_amd64.deb)
- **Fedora/RHEL**: [pasta-tray-X.X.X-1.x86_64.rpm](https://github.com/utensils/pasta/releases/download/vX.X.X/pasta-tray-X.X.X-1.x86_64.rpm)

> **GNOME Users**: Install system tray support:
> ```bash
> # Ubuntu/Debian
> sudo apt install gnome-shell-extension-appindicator
> # Fedora
> sudo dnf install gnome-shell-extension-appindicator
> ```
> Or install from [GNOME Extensions](https://extensions.gnome.org/extension/615/appindicator-support/)

## 🔗 Full Changelog
<!-- Replace X.X.X with the current version and Y.Y.Y with the previous version -->
[vY.Y.Y...vX.X.X](https://github.com/utensils/pasta/compare/vY.Y.Y...vX.X.X)

---
*Built with Tauri v2 and Rust* 🦀