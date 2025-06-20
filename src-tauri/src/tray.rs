use std::sync::Arc;

use log::debug;
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
        let enabled_item = CheckMenuItemBuilder::with_id("enabled", "Enabled")
            .checked(config.enabled)
            .build(app)?;

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
            .item(&enabled_item)
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
                        "enabled" => {
                            let enabled = !config_manager.get().enabled;
                            config_manager.set_enabled(enabled);
                            app.emit("config_changed", ()).unwrap();
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
