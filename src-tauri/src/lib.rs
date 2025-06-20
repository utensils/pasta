mod clipboard;
mod config;
mod keyboard;
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
struct AppState {
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

    info!("Starting Pasta Rust");

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
    use super::*;
    use crate::config::Config;

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
}
