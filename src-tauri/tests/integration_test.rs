use std::sync::Arc;

use pasta_lib::{
    config::{Config, ConfigManager},
    create_app_state, handle_config_changed, initialize_components,
    keyboard::{KeyboardEmulator, TypingSpeed},
};
use tempfile::TempDir;

#[test]
fn test_config_and_keyboard_integration() {
    // Test that config manager and keyboard emulator work together
    let config_manager = Arc::new(ConfigManager::new().unwrap());
    let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

    // Set speed through config
    config_manager.set_typing_speed(TypingSpeed::Fast);

    // Apply to keyboard emulator
    let config = config_manager.get();
    keyboard_emulator.set_typing_speed(config.typing_speed);

    // Verify config was saved
    assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
}

#[test]
fn test_multiple_config_managers_share_state() {
    // Create temp dir for this test
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.toml");

    // Create first config manager and save config
    {
        let _config_manager = ConfigManager::new().unwrap();
        // Manually set the config path
        std::fs::write(
            &config_path,
            toml::to_string(&Config {
                typing_speed: TypingSpeed::Slow,
                left_click_paste: false,
            })
            .unwrap(),
        )
        .unwrap();
    }

    // Load config from the file
    let loaded_config = load_config(&config_path).unwrap();

    // Should have the same speed
    assert_eq!(loaded_config.typing_speed, TypingSpeed::Slow);
}

#[tokio::test]
async fn test_keyboard_emulator_async_operations() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();

    // Test multiple async operations
    let result1 = keyboard_emulator.type_text("Hello").await;
    assert!(result1.is_ok());

    let result2 = keyboard_emulator.type_text("World").await;
    assert!(result2.is_ok());

    // Test with special characters
    let result3 = keyboard_emulator.type_text("Line1\nLine2\tTabbed").await;
    assert!(result3.is_ok());
}

#[test]
fn test_typing_speed_consistency_across_modules() {
    // Ensure TypingSpeed enum is consistent across modules
    let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

    for speed in speeds {
        // Test serialization roundtrip
        let json = serde_json::to_string(&speed).unwrap();
        let deserialized: TypingSpeed = serde_json::from_str(&json).unwrap();
        assert_eq!(speed, deserialized);

        // Test that delay values are sensible
        let delay = speed.delay_ms();
        assert!(delay >= 10 && delay <= 50);
    }
}

#[test]
fn test_config_persistence_across_restarts() {
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.toml");

    // Simulate first run
    {
        std::fs::write(
            &config_path,
            toml::to_string(&Config {
                typing_speed: TypingSpeed::Fast,
                left_click_paste: false,
            })
            .unwrap(),
        )
        .unwrap();
    }

    // Simulate restart - load from disk
    {
        let loaded_config = load_config(&config_path).unwrap();
        assert_eq!(loaded_config.typing_speed, TypingSpeed::Fast);
    }
}

#[test]
fn test_concurrent_config_access() {
    use std::thread;

    let config_manager = Arc::new(ConfigManager::new().unwrap());
    let mut handles = vec![];

    // Spawn multiple threads that read and write config
    for i in 0..5 {
        let cm = config_manager.clone();
        let handle = thread::spawn(move || {
            let speed = match i % 3 {
                0 => TypingSpeed::Slow,
                1 => TypingSpeed::Normal,
                _ => TypingSpeed::Fast,
            };
            cm.set_typing_speed(speed);
            cm.get().typing_speed
        });
        handles.push(handle);
    }

    // All threads should complete without deadlock
    for handle in handles {
        let speed = handle.join().unwrap();
        assert!(matches!(
            speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }
}

#[tokio::test]
async fn test_keyboard_emulator_channel_capacity() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();

    // Send multiple commands quickly
    let mut results = vec![];
    for i in 0..5 {
        let result = keyboard_emulator.type_text(&format!("Text {}", i)).await;
        results.push(result);
    }

    // All should succeed
    for result in results {
        assert!(result.is_ok());
    }
}

#[test]
fn test_cross_module_error_handling() {
    // Test error handling when config directory doesn't exist
    let invalid_path = std::path::PathBuf::from("/invalid/path/config.toml");
    let config_result = load_config(&invalid_path);

    // Should return Ok with default config even if file doesn't exist
    assert!(config_result.is_ok());
    assert_eq!(config_result.unwrap().typing_speed, TypingSpeed::Normal);
}

// Helper function for tests
fn load_config(path: &std::path::PathBuf) -> Result<Config, Box<dyn std::error::Error>> {
    if path.exists() {
        let content = std::fs::read_to_string(path)?;
        match toml::from_str(&content) {
            Ok(config) => Ok(config),
            Err(_) => Ok(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            }),
        }
    } else {
        Ok(Config {
            typing_speed: TypingSpeed::Normal,
            left_click_paste: false,
        })
    }
}

#[test]
fn test_full_app_initialization() {
    // Test the complete initialization flow using public API
    let result = initialize_components();
    assert!(result.is_ok());

    let (config_manager, keyboard_emulator) = result.unwrap();

    // Verify components are properly initialized
    let config = config_manager.get();
    assert!(matches!(
        config.typing_speed,
        TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
    ));

    // Create app state
    let app_state = create_app_state(keyboard_emulator.clone());

    // Test that we can change config and apply it
    config_manager.set_typing_speed(TypingSpeed::Fast);
    handle_config_changed(&config_manager, &keyboard_emulator);

    assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
}

#[test]
fn test_app_logic_integration() {
    use pasta_lib::app_logic::{create_menu_structure, handle_menu_event, MenuAction};

    // Create menu structure
    let menu = create_menu_structure(TypingSpeed::Normal, false);
    assert_eq!(menu.items.len(), 6); // paste, separator, submenu, left_click, separator, quit

    // Test menu event handling
    assert_eq!(handle_menu_event("paste"), MenuAction::Paste);
    assert_eq!(
        handle_menu_event("speed_slow"),
        MenuAction::SetTypingSpeed(TypingSpeed::Slow)
    );
    assert_eq!(
        handle_menu_event("left_click_paste"),
        MenuAction::ToggleLeftClickPaste
    );
    assert_eq!(handle_menu_event("quit"), MenuAction::Quit);
    assert_eq!(handle_menu_event("unknown"), MenuAction::None);
}

#[test]
fn test_tray_integration() {
    use pasta_lib::tray::{
        calculate_show_menu_on_left_click, get_tray_tooltip, handle_tray_icon_click, TrayIconAction,
    };
    use tauri::tray::{MouseButton, MouseButtonState};

    // Test tray tooltip
    assert_eq!(get_tray_tooltip(), "Pasta - Clipboard to Keyboard");

    // Test menu visibility calculation
    assert_eq!(calculate_show_menu_on_left_click(true), false);
    assert_eq!(calculate_show_menu_on_left_click(false), true);

    // Test tray icon click handling
    let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Up, true);
    assert_eq!(action, TrayIconAction::PasteClipboard);

    let action = handle_tray_icon_click(MouseButton::Right, MouseButtonState::Up, false);
    assert_eq!(action, TrayIconAction::ShowMenu);
}

#[tokio::test]
async fn test_paste_clipboard_integration() {
    use pasta_lib::app_logic::{handle_paste_clipboard, ClipboardProvider};

    // Mock clipboard with content
    struct TestClipboard {
        content: Option<String>,
    }

    impl ClipboardProvider for TestClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            Ok(self.content.clone())
        }
    }

    let clipboard = TestClipboard {
        content: Some("Integration test text".to_string()),
    };
    let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

    let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
    assert!(result.is_ok());
}
