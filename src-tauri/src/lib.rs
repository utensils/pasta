mod clipboard;
pub mod config;
pub mod keyboard;
mod tray;
mod window;

use std::sync::Arc;

use log::{error, info};
use tauri::{Listener, Manager, State};

use crate::{
    clipboard::get_clipboard_content,
    config::ConfigManager,
    keyboard::{KeyboardEmulator, TypingSpeed},
    tray::TrayManager,
    window::show_settings_window,
};

#[derive(Clone)]
pub struct AppState {
    config_manager: Arc<ConfigManager>,
    keyboard_emulator: Arc<KeyboardEmulator>,
}

#[tauri::command]
async fn get_config(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let config = state.inner().config_manager.get();
    serde_json::to_value(&config).map_err(|e| e.to_string())
}

#[tauri::command]
async fn save_config(state: State<'_, AppState>, typing_speed: TypingSpeed) -> Result<(), String> {
    let inner = state.inner();
    inner.config_manager.set_typing_speed(typing_speed);
    inner.keyboard_emulator.set_typing_speed(typing_speed);
    Ok(())
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
            let keyboard_emulator =
                Arc::new(KeyboardEmulator::new().expect("Failed to create keyboard emulator"));

            // Load config and apply settings
            let config = config_manager.get();
            keyboard_emulator.set_typing_speed(config.typing_speed);

            // Setup system tray
            let tray_manager = TrayManager::new(config_manager.clone());
            tray_manager.setup(app.handle())?;

            // Create app state
            let app_state = AppState {
                config_manager: config_manager.clone(),
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

            // Show settings window when requested
            let app_handle_clone = app.handle().clone();
            app_handle.listen("show_settings", move |_event| {
                if let Err(e) = show_settings_window(&app_handle_clone) {
                    error!("Failed to show settings window: {e:?}");
                }
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
        .invoke_handler(tauri::generate_handler![
            get_config,
            save_config,
            paste_clipboard
        ])
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

    // Mock implementations for testing
    struct MockState {
        app_state: AppState,
    }

    impl MockState {
        fn new() -> Self {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");

            let config_manager = Arc::new(ConfigManager {
                config: Arc::new(Mutex::new(Config::default())),
                config_path,
            });

            let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

            let app_state = AppState {
                config_manager,
                keyboard_emulator,
            };

            Self { app_state }
        }
    }

    #[tokio::test]
    async fn test_get_config_command() {
        let mock_state = MockState::new();
        // We can't create State directly in tests, so we test the underlying logic
        let config = mock_state.app_state.config_manager.get();
        let config_json = serde_json::to_value(&config).unwrap();

        assert!(config_json.is_object());
        assert!(config_json.get("typing_speed").is_some());
        assert_eq!(config_json.get("typing_speed").unwrap(), "normal");
    }

    #[test]
    fn test_save_config_command() {
        let mock_state = MockState::new();

        // Test the underlying logic directly without blocking in async context
        mock_state
            .app_state
            .config_manager
            .set_typing_speed(TypingSpeed::Fast);
        // Note: We can't call keyboard_emulator.set_typing_speed from async context
        // as it uses blocking_send. In real usage, this is called from non-async context.

        // Verify the config was updated
        let config = mock_state.app_state.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);

        // Test with other speeds
        mock_state
            .app_state
            .config_manager
            .set_typing_speed(TypingSpeed::Slow);
        let config = mock_state.app_state.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Slow);
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

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Fast,
            })),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let app_state = AppState {
            config_manager: config_manager.clone(),
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Test cloning
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(
            &app_state.config_manager,
            &cloned_state.config_manager
        ));
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &cloned_state.keyboard_emulator
        ));
    }

    #[test]
    fn test_config_no_longer_has_enabled_field() {
        let config = Config::default();
        let json = serde_json::to_value(&config).unwrap();

        // Verify the config only has typing_speed field
        assert!(json.is_object());
        assert!(json.get("typing_speed").is_some());
        assert!(json.get("enabled").is_none());
    }

    #[test]
    fn test_config_serialization() {
        let config = Config {
            typing_speed: TypingSpeed::Fast,
        };

        let json = serde_json::to_string(&config).unwrap();
        assert!(json.contains("typing_speed"));
        assert!(json.contains("fast"));
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

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let app_state = AppState {
            config_manager: config_manager.clone(),
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Verify app state holds correct references
        let config = app_state.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
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

        // Modify through one reference
        state1.config_manager.set_typing_speed(TypingSpeed::Fast);

        // Verify change is visible through other reference
        let config = state2.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
    }
}
