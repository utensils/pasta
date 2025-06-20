mod clipboard;
mod config;
mod keyboard;
mod tray;

use crate::clipboard::{ClipboardEvent, ClipboardMonitor};
use crate::config::ConfigManager;
use crate::keyboard::{KeyboardEmulator, TypingSpeed};
use crate::tray::TrayManager;
use log::{error, info};
use std::sync::Arc;
use tauri::{AppHandle, Listener, Manager, State};
use tokio::sync::mpsc;

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
            // Initialize components
            let config_manager = Arc::new(ConfigManager::new().expect("Failed to create config manager"));
            let clipboard_monitor = Arc::new(ClipboardMonitor::new().expect("Failed to create clipboard monitor"));
            let keyboard_emulator = Arc::new(KeyboardEmulator::new().expect("Failed to create keyboard emulator"));

            // Load config and apply settings
            let config = config_manager.get();
            clipboard_monitor.set_enabled(config.enabled);
            keyboard_emulator.set_typing_speed(config.typing_speed);

            // Setup system tray
            let tray_manager = TrayManager::new(config_manager.clone());
            tray_manager.setup(&app.handle())?;

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
                        error!("Clipboard monitoring error: {:?}", e);
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
                                    error!("Failed to type text: {:?}", e);
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
                if let Some(window) = app_handle_clone.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                } else {
                    // Create settings window if it doesn't exist
                    create_settings_window(&app_handle_clone);
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_config, save_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn create_settings_window(app: &AppHandle) {
    tauri::WebviewWindowBuilder::new(
        app,
        "main",
        tauri::WebviewUrl::App("index.html".into()),
    )
    .title("Pasta Settings")
    .inner_size(400.0, 300.0)
    .resizable(false)
    .build()
    .expect("Failed to create settings window");
}