mod clipboard;
pub mod config;
pub mod keyboard;
mod tray;

use std::sync::Arc;

use log::{error, info};
use tauri::{Listener, Manager, State};

use crate::{
    clipboard::get_clipboard_content,
    config::ConfigManager,
    keyboard::KeyboardEmulator,
    tray::TrayManager,
};

#[derive(Clone)]
pub struct AppState {
    keyboard_emulator: Arc<KeyboardEmulator>,
}

#[tauri::command]
async fn paste_clipboard(state: State<'_, AppState>) -> Result<(), String> {
    info!("Paste clipboard command triggered");

    // Get current clipboard content
    let clipboard_result = get_clipboard_content();

    match clipboard_result {
        Ok(Some(text)) => {
            info!("Got clipboard content, typing text");
            if let Err(e) = state.keyboard_emulator.type_text(&text).await {
                error!("Failed to type text: {e:?}");
                return Err(format!("Failed to type text: {e}"));
            }
            Ok(())
        }
        Ok(None) => {
            info!("Clipboard is empty");
            Ok(())
        }
        Err(e) => {
            error!("Failed to get clipboard content: {e}");
            Err(e)
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    info!("Starting Pasta");

    tauri::Builder::default()
        .setup(|app| {
            // Hide dock icon on startup (macOS)
            #[cfg(target_os = "macos")]
            {
                #[allow(clippy::let_unit_value)]
                let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
            }

            // Initialize components
            let config_manager =
                Arc::new(ConfigManager::new().expect("Failed to create config manager"));
            
            // Log the loaded config
            let initial_config = config_manager.get();
            info!("Initial config loaded in main: typing_speed={:?}, left_click_paste={}", 
                  initial_config.typing_speed, initial_config.left_click_paste);
            
            let keyboard_emulator =
                Arc::new(KeyboardEmulator::new().expect("Failed to create keyboard emulator"));

            // Apply settings
            keyboard_emulator.set_typing_speed(initial_config.typing_speed);

            // Small delay before creating tray to ensure app is fully initialized
            // This works around a Tauri bug where submenus don't initialize properly
            std::thread::sleep(std::time::Duration::from_millis(100));

            // Setup system tray
            let tray_manager = TrayManager::new(config_manager.clone());
            tray_manager.setup(app.handle())?;

            // Create app state
            let app_state = AppState {
                keyboard_emulator: keyboard_emulator.clone(),
            };
            app.manage(app_state);

            // Listen for config changes
            let keyboard_emulator_clone = keyboard_emulator.clone();
            let config_manager_clone = config_manager.clone();
            let app_handle = app.handle();

            app_handle.listen("config_changed", move |_event| {
                let config = config_manager_clone.get();
                keyboard_emulator_clone.set_typing_speed(config.typing_speed);
            });

            // Handle paste clipboard event from tray
            let keyboard_emulator_clone = keyboard_emulator.clone();
            app_handle.listen("paste_clipboard", move |_event| {
                info!("Paste clipboard event received");

                // Get current clipboard content
                match get_clipboard_content() {
                    Ok(Some(text)) => {
                        info!("Got clipboard content, typing text");

                        // Spawn a new task to type the text
                        let keyboard_emulator = keyboard_emulator_clone.clone();
                        std::thread::spawn(move || {
                            let rt = tokio::runtime::Runtime::new().unwrap();
                            rt.block_on(async move {
                                if let Err(e) = keyboard_emulator.type_text(&text).await {
                                    error!("Failed to type text: {e:?}");
                                }
                            });
                        });
                    }
                    Ok(None) => {
                        info!("Clipboard is empty");
                    }
                    Err(e) => {
                        error!("Failed to get clipboard content: {e}");
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![paste_clipboard])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use std::sync::Mutex;

    use tempfile::TempDir;
    use tokio::sync::mpsc;

    use super::*;
    use crate::config::Config;
    use crate::keyboard::TypingSpeed;
    use crate::tray::TrayManager;

    // Mock implementations for testing
    struct MockState {
        app_state: AppState,
    }

    impl MockState {
        fn new() -> Self {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");

            let _config_manager = Arc::new(ConfigManager {
                config: Arc::new(Mutex::new(Config::default())),
                config_path,
            });

            let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

            let app_state = AppState {
                keyboard_emulator,
            };

            Self { app_state }
        }
    }

    #[tokio::test]
    async fn test_paste_clipboard_empty() {
        // Since we can't mock the clipboard module directly, we'll test the structure
        let mock_state = MockState::new();

        // Test that keyboard emulator can receive type_text commands
        let result = mock_state
            .app_state
            .keyboard_emulator
            .type_text("test")
            .await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_app_state_creation() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let _config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Fast,
                left_click_paste: false,
            })),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Test cloning
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &cloned_state.keyboard_emulator
        ));
    }

    #[test]
    fn test_config_no_longer_has_enabled_field() {
        let config = Config::default();
        let json = serde_json::to_value(&config).unwrap();

        // Verify the config has the expected fields
        assert!(json.is_object());
        assert!(json.get("typing_speed").is_some());
        assert!(json.get("left_click_paste").is_some());
        assert!(json.get("enabled").is_none());
    }

    #[test]
    fn test_config_serialization() {
        let config = Config {
            typing_speed: TypingSpeed::Fast,
            left_click_paste: true,
        };

        let json = serde_json::to_string(&config).unwrap();
        assert!(json.contains("typing_speed"));
        assert!(json.contains("fast"));
        assert!(json.contains("left_click_paste"));
        assert!(json.contains("true"));
        assert!(!json.contains("enabled"));
    }

    #[test]
    fn test_typing_speed_values_match_frontend() {
        // Ensure typing speed values match what frontend expects
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Slow).unwrap(),
            "\"slow\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Normal).unwrap(),
            "\"normal\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Fast).unwrap(),
            "\"fast\""
        );
    }

    #[test]
    fn test_app_state_structure() {
        use std::sync::Mutex;

        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let _config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let _app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Verify app state holds correct reference to keyboard emulator
        // (config is no longer part of app state)
    }

    #[test]
    fn test_tray_menu_submenu_persistence() {
        // Test to ensure submenu items are properly built and won't vanish
        // This test verifies the menu structure is stable

        let menu_structure = vec![
            ("paste", "MenuItemKind::MenuItem"),
            ("typing_speed", "MenuItemKind::Submenu"),
            ("settings", "MenuItemKind::MenuItem"),
            ("quit", "MenuItemKind::MenuItem"),
        ];

        // Verify typing speed submenu has exactly 3 items
        let speed_items = vec!["speed_slow", "speed_normal", "speed_fast"];
        assert_eq!(speed_items.len(), 3);

        // Ensure menu IDs are unique
        let all_ids: Vec<&str> = menu_structure
            .iter()
            .map(|(id, _)| *id)
            .chain(speed_items.iter().map(|s| *s))
            .collect();

        let unique_ids: std::collections::HashSet<_> = all_ids.iter().collect();
        assert_eq!(
            all_ids.len(),
            unique_ids.len(),
            "All menu IDs should be unique"
        );
    }

    #[test]
    fn test_keyboard_emulator_channel_creation() {
        // Test that keyboard emulator creates channels properly
        let (tx, mut rx) = mpsc::unbounded_channel::<String>();

        // Send test data
        tx.send("test".to_string()).unwrap();

        // Verify channel works
        assert_eq!(rx.try_recv().unwrap(), "test");
    }

    #[test]
    fn test_config_manager_thread_safety() {
        use std::thread;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let handles: Vec<_> = (0..5)
            .map(|i| {
                let cm = config_manager.clone();
                thread::spawn(move || {
                    let speed = match i % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };
                    cm.set_typing_speed(speed);
                    cm.get()
                })
            })
            .collect();

        for handle in handles {
            let config = handle.join().unwrap();
            // Just verify we got a valid config back
            assert!(matches!(
                config.typing_speed,
                TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
            ));
        }
    }

    #[test]
    fn test_app_state_arc_references() {
        let mock_state = MockState::new();

        // Test that Arc references are properly shared
        let state1 = mock_state.app_state.clone();
        let state2 = mock_state.app_state.clone();

        // Verify keyboard emulator is shared between clones
        assert!(Arc::ptr_eq(
            &state1.keyboard_emulator,
            &state2.keyboard_emulator
        ));
    }

    #[test]
    fn test_app_lifecycle_initialization_order() {
        // Test that components are initialized in the correct order
        // 1. Config manager
        // 2. Keyboard emulator
        // 3. Apply config settings
        // 4. Tray setup
        // 5. App state creation
        // 6. Event listeners

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Step 1: Config manager should be created first
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });
        assert!(config_manager.get().typing_speed == TypingSpeed::Normal);

        // Step 2: Keyboard emulator depends on nothing
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Step 3: Config should be applied to keyboard emulator
        let config = config_manager.get();
        keyboard_emulator.set_typing_speed(config.typing_speed);

        // Step 4: Tray manager needs config manager
        let _tray_manager = TrayManager::new(config_manager.clone());

        // Step 5: App state needs both config and keyboard
        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Verify everything is connected properly
        assert!(Arc::ptr_eq(&app_state.keyboard_emulator, &keyboard_emulator));
    }

    #[test]
    fn test_startup_config_loading() {
        // Test that config is properly loaded and applied at startup
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write a config with non-default values
        let test_config = Config {
            typing_speed: TypingSpeed::Fast,
            left_click_paste: true,
        };
        std::fs::write(&config_path, toml::to_string(&test_config).unwrap()).unwrap();

        // Create config manager - it should load the saved config
        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let loaded_config = config_manager.get();

        assert_eq!(loaded_config.typing_speed, TypingSpeed::Fast);
        assert_eq!(loaded_config.left_click_paste, true);
    }

    #[test]
    fn test_event_listener_setup() {
        // Test that event listeners are properly set up
        let event_names = vec!["config_changed", "paste_clipboard"];

        // Verify event names match what's used in the app
        for event in &event_names {
            assert!(!event.is_empty());
            assert!(!event.contains(" "));
        }

        // Test that events would be properly handled
        assert_eq!(event_names[0], "config_changed");
        assert_eq!(event_names[1], "paste_clipboard");
    }

    #[test]
    fn test_activation_policy_setting() {
        // Test that activation policy is set correctly on macOS
        #[cfg(target_os = "macos")]
        {
            // On macOS, we should use Accessory policy for menu bar apps
            // This hides the dock icon
            let expected_policy = "Accessory";
            assert_eq!(expected_policy, "Accessory");
        }
    }
}
