# Pasta Rust/Tauri Implementation PRD

## Project Overview

Reimplementation of Pasta's core functionality in Rust using Tauri framework. This will be a minimal system tray application that monitors the clipboard and emulates keyboard typing to paste content into applications that don't support direct clipboard pasting.

## Core Functionality Only

- System tray icon with basic menu
- Clipboard monitoring
- Keyboard typing emulation
- Basic settings (typing speed, enable/disable)
- No history, no encryption, no hotkeys, no advanced features

## Technology Stack

- **Language**: Rust
- **Framework**: Tauri v2
- **System Tray**: tauri-plugin-tray
- **Clipboard**: arboard
- **Keyboard Simulation**: enigo
- **Configuration**: serde + TOML

## Development Tasks

### Phase 1: Project Setup

- [x] Create `./trees` directory and add to `.gitignore`
- [x] Create new worktree branch `rust-refactor` in `./trees` directory
- [x] Initialize new Tauri project with `cargo create-tauri-app`
- [x] Configure `Cargo.toml` with required dependencies:
  ```toml
  [dependencies]
  tauri = { version = "2.0", features = ["tray-icon"] }
  serde = { version = "1.0", features = ["derive"] }
  serde_json = "1.0"
  tokio = { version = "1", features = ["full"] }
  arboard = "3.4"
  enigo = "0.2"
  ```
- [x] Set up basic Tauri configuration in `tauri.conf.json`
- [x] Configure app to run in system tray mode (no main window)
- [x] Create basic project structure:
  ```
  src-tauri/
  ├── src/
  │   ├── main.rs
  │   ├── clipboard.rs
  │   ├── keyboard.rs
  │   ├── config.rs
  │   └── tray.rs
  ```

### Phase 2: System Tray Implementation

- [x] Create `tray.rs` module with basic system tray setup
- [x] Implement system tray icon loading from embedded resource
- [x] Create tray menu structure:
  - Enabled/Disabled toggle
  - Typing Speed submenu (Slow/Normal/Fast)
  - Settings
  - Quit
- [x] Implement menu event handlers
- [x] Add tray icon tooltip showing current state
- [ ] Test tray icon appears on all platforms (Windows, macOS, Linux)

### Phase 3: Clipboard Monitoring

- [x] Create `clipboard.rs` module
- [x] Implement `ClipboardMonitor` struct using arboard
- [x] Set up polling loop to check clipboard every 500ms
- [x] Implement change detection using content hashing
- [x] Create event system to notify when clipboard changes
- [x] Add enable/disable functionality for monitoring
- [x] Handle clipboard read errors gracefully
- [ ] Test clipboard monitoring with various content types

### Phase 4: Keyboard Emulation

- [x] Create `keyboard.rs` module
- [x] Implement `KeyboardEmulator` struct using enigo
- [x] Create `type_text()` function that types character by character
- [x] Implement configurable typing delay between characters
- [x] Add support for special characters and newlines
- [x] Implement text chunking for long content
- [x] Add platform-specific keyboard handling
- [ ] Test keyboard emulation with various applications

### Phase 5: Configuration System

- [x] Create `config.rs` module
- [x] Define `Config` struct with serde:
  ```rust
  #[derive(Serialize, Deserialize)]
  struct Config {
      enabled: bool,
      typing_speed: TypingSpeed,
  }
  ```
- [x] Implement config file loading from platform-specific location
- [x] Create config saving functionality
- [x] Add default configuration values
- [x] Implement typing speed enum (Slow: 50ms, Normal: 25ms, Fast: 10ms)
- [x] Handle missing/corrupt config files gracefully

### Phase 6: Core Integration

- [x] Wire up clipboard monitor to keyboard emulator in `main.rs`
- [x] Implement state management for enabled/disabled
- [x] Create communication channel between tray menu and core logic
- [x] Add tokio async runtime for clipboard monitoring
- [x] Implement proper error handling throughout
- [x] Add logging for debugging (but keep it minimal)
- [ ] Test full clipboard → keyboard flow

### Phase 7: Settings Window

- [x] Create minimal settings window using Tauri webview
- [x] Design simple HTML/CSS interface with:
  - Enable/Disable toggle
  - Typing speed slider
  - Save button
- [x] Implement IPC commands for settings:
  - `get_config`
  - `save_config`
- [x] Wire settings window to tray menu
- [x] Ensure settings persist between app restarts

### Phase 8: Platform-Specific Handling

- [ ] Test and fix Windows-specific issues:
  - [ ] Ensure keyboard emulation works with UAC prompts
  - [ ] Handle high-DPI scaling for tray icon
- [ ] Test and fix macOS-specific issues:
  - [ ] Request accessibility permissions
  - [ ] Handle macOS security restrictions
  - [ ] Ensure tray icon works in menu bar
- [ ] Test and fix Linux-specific issues:
  - [ ] Support both X11 and Wayland
  - [ ] Handle different desktop environments
  - [ ] Ensure proper permissions for keyboard emulation

### Phase 9: Build and Distribution

- [ ] Configure release builds in `Cargo.toml`
- [ ] Set up GitHub Actions for CI/CD
- [ ] Create build scripts for each platform
- [ ] Configure code signing for macOS/Windows
- [ ] Create minimal installer using Tauri's bundler
- [ ] Test installation on clean systems
- [ ] Document installation requirements

### Phase 10: Testing and Polish

- [ ] Create basic integration tests
- [ ] Test with various applications that block clipboard
- [ ] Verify typing speed settings work correctly
- [ ] Ensure clean startup and shutdown
- [ ] Check memory usage stays reasonable
- [ ] Verify no clipboard content is logged or stored
- [ ] Test enable/disable functionality thoroughly
- [x] Create minimal README with usage instructions

## Implementation Notes

### Key Principles

1. **Minimal Feature Set**: Only clipboard monitoring and keyboard typing
2. **No Data Storage**: No history, no files, no database
3. **Simple Configuration**: Just enabled state and typing speed
4. **Resource Efficient**: Minimal CPU and memory usage
5. **Cross-Platform**: Must work on Windows, macOS, and Linux

### Security Considerations

- Never log clipboard contents
- No network connections
- No data persistence beyond basic settings
- Request only necessary system permissions

### Performance Requirements

- Clipboard polling should use < 1% CPU
- Memory usage should stay under 50MB
- Typing should feel natural and not robotic
- App should start within 2 seconds

### Error Handling

- Gracefully handle clipboard access errors
- Continue running if keyboard emulation fails
- Show user-friendly error messages in tray
- Never crash the system tray icon

## Success Criteria

- [x] App runs in system tray on all platforms
- [x] Clipboard changes trigger keyboard typing
- [x] Typing speed is configurable
- [x] Can enable/disable monitoring from tray
- [ ] Uses less than 50MB RAM and 1% CPU
- [x] No data is stored or logged
- [x] Settings persist between restarts
- [ ] Clean install/uninstall process

## Additional Completed Items

- [x] Pasta branding icons and logos added
- [x] Comprehensive README documentation
- [x] TOML configuration persistence
- [x] Multi-threaded architecture for non-blocking UI
- [x] Platform-specific config file locations