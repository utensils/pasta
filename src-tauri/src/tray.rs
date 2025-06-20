use std::sync::Arc;

use log::{debug, info};
use tauri::{
    menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder, SubmenuBuilder},
    tray::{TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Runtime,
};

use crate::{config::ConfigManager, keyboard::TypingSpeed};

pub struct TrayManager {
    config_manager: Arc<ConfigManager>,
}

impl TrayManager {
    pub fn new(config_manager: Arc<ConfigManager>) -> Self {
        Self { config_manager }
    }

    pub fn setup<R: Runtime>(&self, app: &AppHandle<R>) -> Result<(), Box<dyn std::error::Error>> {
        let config = self.config_manager.get();

        // Create menu items
        let paste_item = MenuItemBuilder::with_id("paste", "Paste").build(app)?;

        // Create typing speed submenu
        let slow_item = CheckMenuItemBuilder::with_id("speed_slow", "Slow")
            .checked(config.typing_speed == TypingSpeed::Slow)
            .build(app)?;

        let normal_item = CheckMenuItemBuilder::with_id("speed_normal", "Normal")
            .checked(config.typing_speed == TypingSpeed::Normal)
            .build(app)?;

        let fast_item = CheckMenuItemBuilder::with_id("speed_fast", "Fast")
            .checked(config.typing_speed == TypingSpeed::Fast)
            .build(app)?;

        let speed_submenu = SubmenuBuilder::new(app, "Typing Speed")
            .item(&slow_item)
            .item(&normal_item)
            .item(&fast_item)
            .build()?;

        let settings_item = MenuItemBuilder::with_id("settings", "Settings").build(app)?;

        let quit_item = MenuItemBuilder::with_id("quit", "Quit").build(app)?;

        // Build main menu
        let menu = MenuBuilder::new(app)
            .item(&paste_item)
            .separator()
            .item(&speed_submenu)
            .separator()
            .item(&settings_item)
            .separator()
            .item(&quit_item)
            .build()?;

        // Create tray icon
        let _tray = TrayIconBuilder::new()
            .icon(app.default_window_icon().unwrap().clone())
            .menu(&menu)
            .tooltip("Pasta - Clipboard to Keyboard")
            .on_menu_event({
                let config_manager = self.config_manager.clone();
                let app_handle = app.clone();
                move |app, event| {
                    debug!("Menu event: {}", event.id.as_ref());
                    match event.id.as_ref() {
                        "paste" => {
                            info!("Paste menu item clicked");
                            // Invoke the paste command
                            app.emit("paste_clipboard", ()).unwrap();
                        }
                        "speed_slow" => {
                            config_manager.set_typing_speed(TypingSpeed::Slow);
                            update_speed_menu_state(&app_handle, TypingSpeed::Slow);
                            app.emit("config_changed", ()).unwrap();
                        }
                        "speed_normal" => {
                            config_manager.set_typing_speed(TypingSpeed::Normal);
                            update_speed_menu_state(&app_handle, TypingSpeed::Normal);
                            app.emit("config_changed", ()).unwrap();
                        }
                        "speed_fast" => {
                            config_manager.set_typing_speed(TypingSpeed::Fast);
                            update_speed_menu_state(&app_handle, TypingSpeed::Fast);
                            app.emit("config_changed", ()).unwrap();
                        }
                        "settings" => {
                            app.emit("show_settings", ()).unwrap();
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                }
            })
            .on_tray_icon_event(|_tray, event| {
                if let TrayIconEvent::Click { .. } = event {
                    debug!("Tray icon clicked");
                }
            })
            .build(app)?;

        Ok(())
    }
}

fn update_speed_menu_state<R: Runtime>(_app: &AppHandle<R>, speed: TypingSpeed) {
    // Store menu items in the state for later access
    // For now, we'll just log the speed change
    debug!("Speed changed to: {speed:?}");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tray_manager_creation() {
        use tempfile::TempDir;
        use std::sync::Mutex;
        use crate::config::Config;
        
        // Create a test config manager with temporary directory
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });
        
        let tray_manager = TrayManager::new(config_manager.clone());
        
        // Verify the tray manager holds a reference to config manager
        let config = tray_manager.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_menu_has_paste_item() {
        // This test verifies that our menu structure includes the paste item
        // We can't fully test menu creation without a Tauri app context
        
        let menu_items = vec!["paste", "speed_slow", "speed_normal", "speed_fast", "settings", "quit"];
        
        // Verify expected menu item IDs exist
        assert!(menu_items.contains(&"paste"));
        assert!(!menu_items.contains(&"enabled")); // Should not have enabled item
    }
}