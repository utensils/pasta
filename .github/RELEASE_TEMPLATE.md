# Release vX.X.X

## What's Changed
<!-- List major changes here -->

## Downloads
<!-- Release artifacts will be attached automatically -->

### Platform-Specific Notes

#### macOS
- The app is unsigned. Remove quarantine with: `xattr -d com.apple.quarantine /Applications/Pasta.app`
- Requires accessibility permissions for keyboard emulation

#### Linux
- **GNOME Users**: You need to install a system tray extension:
  ```bash
  # Ubuntu/Debian
  sudo apt install gnome-shell-extension-appindicator
  
  # Fedora
  sudo dnf install gnome-shell-extension-appindicator
  
  # Arch
  sudo pacman -S gnome-shell-extension-appindicator
  ```
  Or install from [GNOME Extensions](https://extensions.gnome.org/extension/615/appindicator-support/)
- Other desktop environments (KDE, XFCE, etc.) have native system tray support

#### Windows
- Works out of the box
- May trigger antivirus warnings due to keyboard emulation

## Full Changelog
<!-- Link to compare view will be added -->

---
*Built with Tauri v2 and Rust*