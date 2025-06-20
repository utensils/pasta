mod clipboard;
mod config;
mod keyboard;
mod tray;
mod window;

use std::sync::Arc;

use log::{error, info};
use tauri::{Listener, Manager, State};
use tokio::sync::mpsc;

use crate::{
    clipboard::{ClipboardEvent, ClipboardMonitor},
    config::ConfigManager,
    keyboard::{KeyboardEmulator, TypingSpeed},
    tray::TrayManager,
    window::show_settings_window,
};

#[derive(Clone)]
struct AppState {
    config_manager: Arc<ConfigManager>,
    clipboard_monitor: Arc<ClipboardMonitor>,
    keyboard_emulator: Arc<KeyboardEmulator>,
}

#[tauri::command]
async fn get_config(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let config = state.inner().config_manager.get();
    serde_json::to_value(&config).map_err(|e| e.to_string())
}

#[tauri::command]
async fn save_config(
    state: State<'_, AppState>,
    enabled: bool,
    typing_speed: TypingSpeed,
) -> Result<(), String> {
    let inner = state.inner();
    inner.config_manager.set_enabled(enabled);
    inner.config_manager.set_typing_speed(typing_speed);
    inner.clipboard_monitor.set_enabled(enabled);
    inner.keyboard_emulator.set_typing_speed(typing_speed);
    Ok(())
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
                let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
            }
            
            // Initialize components
            let config_manager =
                Arc::new(ConfigManager::new().expect("Failed to create config manager"));
            let clipboard_monitor =
                Arc::new(ClipboardMonitor::new().expect("Failed to create clipboard monitor"));
            let keyboard_emulator =
                Arc::new(KeyboardEmulator::new().expect("Failed to create keyboard emulator"));

            // Load config and apply settings
            let config = config_manager.get();
            clipboard_monitor.set_enabled(config.enabled);
            keyboard_emulator.set_typing_speed(config.typing_speed);

            // Setup system tray
            let tray_manager = TrayManager::new(config_manager.clone());
            tray_manager.setup(app.handle())?;

            // Create app state
            let app_state = AppState {
                config_manager: config_manager.clone(),
                clipboard_monitor: clipboard_monitor.clone(),
                keyboard_emulator: keyboard_emulator.clone(),
            };
            app.manage(app_state);

            // Start clipboard monitoring in a separate thread with its own runtime
            let (tx, mut rx) = mpsc::channel::<ClipboardEvent>(10);
            let clipboard_monitor_clone = clipboard_monitor.clone();
            let keyboard_emulator_clone = keyboard_emulator.clone();

            std::thread::spawn(move || {
                let rt = tokio::runtime::Runtime::new().unwrap();
                rt.block_on(async move {
                    if let Err(e) = clipboard_monitor_clone.start_monitoring(tx).await {
                        error!("Clipboard monitoring error: {e:?}");
                    }
                });
            });

            // Handle clipboard events in another thread
            std::thread::spawn(move || {
                let rt = tokio::runtime::Runtime::new().unwrap();
                rt.block_on(async move {
                    while let Some(event) = rx.recv().await {
                        match event {
                            ClipboardEvent::ContentChanged(text) => {
                                info!("Clipboard changed, typing text");
                                if let Err(e) = keyboard_emulator_clone.type_text(&text).await {
                                    error!("Failed to type text: {e:?}");
                                }
                            }
                        }
                    }
                });
            });

            // Listen for config changes
            let clipboard_monitor_clone = clipboard_monitor.clone();
            let keyboard_emulator_clone = keyboard_emulator.clone();
            let config_manager_clone = config_manager.clone();
            let app_handle = app.handle();

            app_handle.listen("config_changed", move |_event| {
                let config = config_manager_clone.get();
                clipboard_monitor_clone.set_enabled(config.enabled);
                keyboard_emulator_clone.set_typing_speed(config.typing_speed);
            });

            // Show settings window when requested
            let app_handle_clone = app.handle().clone();
            app_handle.listen("show_settings", move |_event| {
                if let Err(e) = show_settings_window(&app_handle_clone) {
                    error!("Failed to show settings window: {e:?}");
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_config, save_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

