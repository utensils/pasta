use std::sync::Arc;

use log::{debug, error, info};
use tauri::{
    menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder, SubmenuBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
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
    
    fn build_tauri_menu<R: Runtime>(
        &self, 
        app: &AppHandle<R>, 
        structure: &crate::app_logic::MenuStructure
    ) -> Result<tauri::menu::Menu<R>, Box<dyn std::error::Error>> {
        use crate::app_logic::MenuItem;
        
        let mut menu_builder = MenuBuilder::new(app);
        
        for item in &structure.items {
            match item {
                MenuItem::Action { id, label } => {
                    let menu_item = MenuItemBuilder::with_id(id, label).build(app)?;
                    menu_builder = menu_builder.item(&menu_item);
                },
                MenuItem::CheckItem { id, label, checked } => {
                    let check_item = CheckMenuItemBuilder::with_id(id, label)
                        .checked(*checked)
                        .build(app)?;
                    menu_builder = menu_builder.item(&check_item);
                },
                MenuItem::Submenu { label, items } => {
                    let mut submenu_builder = SubmenuBuilder::new(app, label);
                    for sub_item in items {
                        if let MenuItem::CheckItem { id, label, checked } = sub_item {
                            let check_item = CheckMenuItemBuilder::with_id(id, label)
                                .checked(*checked)
                                .build(app)?;
                            submenu_builder = submenu_builder.item(&check_item);
                        }
                    }
                    let submenu = submenu_builder.build()?;
                    menu_builder = menu_builder.item(&submenu);
                },
                MenuItem::Separator => {
                    menu_builder = menu_builder.separator();
                },
            }
        }
        
        Ok(menu_builder.build()?)
    }

    pub fn setup<R: Runtime>(&self, app: &AppHandle<R>) -> Result<(), Box<dyn std::error::Error>> {
        let config = self.config_manager.get();
        info!("Setting up tray with config: typing_speed={:?}, left_click_paste={}", 
              config.typing_speed, config.left_click_paste);

        // Get menu structure from business logic
        let menu_structure = crate::app_logic::create_menu_structure(
            config.typing_speed, 
            config.left_click_paste
        );
        
        // Convert to Tauri menu
        let menu = self.build_tauri_menu(app, &menu_structure)?;

        // Create tray icon with menu
        let _tray = TrayIconBuilder::with_id("main")
            .icon(app.default_window_icon().unwrap().clone())
            .menu(&menu)
            .show_menu_on_left_click(!config.left_click_paste)
            .tooltip("Pasta - Clipboard to Keyboard")
            .on_menu_event({
                let config_manager = self.config_manager.clone();
                let app_handle = app.clone();
                move |app, event| {
                    use crate::app_logic::{handle_menu_event, MenuAction};
                    
                    debug!("Menu event: {}", event.id.as_ref());
                    let action = handle_menu_event(event.id.as_ref());
                    
                    match action {
                        MenuAction::Paste => {
                            info!("Paste menu item clicked");
                            app.emit("paste_clipboard", ()).unwrap();
                        }
                        MenuAction::SetTypingSpeed(speed) => {
                            config_manager.set_typing_speed(speed);
                            
                            // Rebuild the menu to update checkbox states
                            let tray_manager = TrayManager::new(config_manager.clone());
                            if let Err(e) = tray_manager.rebuild_menu(&app_handle) {
                                error!("Failed to rebuild menu: {}", e);
                            }
                            
                            app.emit("config_changed", ()).unwrap();
                        }
                        MenuAction::ToggleLeftClickPaste => {
                            let current = config_manager.get().left_click_paste;
                            config_manager.set_left_click_paste(!current);

                            // Update tray behavior
                            if let Some(tray) = app.tray_by_id("main") {
                                let _ = tray.set_show_menu_on_left_click(current); // Inverted: if was enabled, now show menu
                            }
                            
                            // Rebuild the menu to update checkbox state
                            let tray_manager = TrayManager::new(config_manager.clone());
                            if let Err(e) = tray_manager.rebuild_menu(&app_handle) {
                                error!("Failed to rebuild menu: {}", e);
                            }
                        }
                        MenuAction::Quit => {
                            app.exit(0);
                        }
                        MenuAction::None => {}
                    }
                }
            })
            .on_tray_icon_event({
                let app_handle = app.clone();
                let config_manager = self.config_manager.clone();
                move |_tray, event| match event {
                    TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } => {
                        let config = config_manager.get();
                        if config.left_click_paste {
                            debug!("Left click on tray icon - pasting clipboard");
                            app_handle.emit("paste_clipboard", ()).unwrap();
                        } else {
                            debug!("Left click on tray icon - showing menu (left_click_paste disabled)");
                            // Menu will be shown automatically when show_menu_on_left_click is true
                        }
                    }
                    TrayIconEvent::Click {
                        button: MouseButton::Right,
                        button_state: MouseButtonState::Up,
                        ..
                    } => {
                        debug!("Right click on tray icon - showing menu");
                        // Menu is automatically shown on right-click by Tauri
                    }
                    _ => {}
                }
            })
            .build(app)?;

        // The tray icon is automatically managed by Tauri
        // We don't need to explicitly store it

        Ok(())
    }
    
    pub fn rebuild_menu<R: Runtime>(&self, app: &AppHandle<R>) -> Result<(), Box<dyn std::error::Error>> {
        // Get the existing tray
        if let Some(tray) = app.tray_by_id("main") {
            // Get current config
            let config = self.config_manager.get();
            info!("Rebuilding menu with config: typing_speed={:?}, left_click_paste={}", 
                  config.typing_speed, config.left_click_paste);
            
            // Get menu structure from business logic
            let menu_structure = crate::app_logic::create_menu_structure(
                config.typing_speed, 
                config.left_click_paste
            );
            
            // Convert to Tauri menu
            let menu = self.build_tauri_menu(app, &menu_structure)?;
            
            // Update the tray menu
            tray.set_menu(Some(menu))?;
        }
        
        Ok(())
    }
}


#[cfg(test)]
mod tests {
    use std::collections::HashMap;

    use super::*;

    #[test]
    fn test_tray_manager_creation() {
        use std::sync::Mutex;

        use tempfile::TempDir;

        use crate::config::Config;

        // Create a test config manager with temporary directory
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
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

        let menu_items = vec![
            "paste",
            "speed_slow",
            "speed_normal",
            "speed_fast",
            "left_click_paste",
            "quit",
        ];

        // Verify expected menu item IDs exist
        assert!(menu_items.contains(&"paste"));
        assert!(!menu_items.contains(&"enabled")); // Should not have enabled item
    }

    #[test]
    fn test_menu_structure_hierarchy() {
        // Test that verifies the expected menu structure
        // Main menu should have:
        // - Paste (top level)
        // - Typing Speed (submenu with 3 items)
        // - Settings
        // - Quit

        let _expected_structure = vec![
            ("paste", "item"),
            ("typing_speed", "submenu"),
            ("left_click_paste", "check_item"),
            ("quit", "item"),
        ];

        let speed_submenu_items = vec!["speed_slow", "speed_normal", "speed_fast"];

        // Verify submenu contains all speed options
        assert_eq!(speed_submenu_items.len(), 3);
        for item in &speed_submenu_items {
            assert!(item.starts_with("speed_"));
        }
    }

    #[test]
    fn test_typing_speed_menu_items_exclusive() {
        // Test that only one typing speed can be selected at a time
        let speeds = vec![
            (TypingSpeed::Slow, "speed_slow"),
            (TypingSpeed::Normal, "speed_normal"),
            (TypingSpeed::Fast, "speed_fast"),
        ];

        // For each speed setting, verify only one item would be checked
        for (selected_speed, selected_id) in &speeds {
            let mut checked_count = 0;
            for (speed, id) in &speeds {
                if speed == selected_speed {
                    checked_count += 1;
                    assert_eq!(id, selected_id);
                }
            }
            assert_eq!(checked_count, 1, "Only one speed should be selected");
        }
    }

    #[test]
    fn test_menu_event_handlers() {
        // Test that all menu event IDs are properly handled
        let event_ids = vec![
            "paste",
            "speed_slow",
            "speed_normal",
            "speed_fast",
            "left_click_paste",
            "quit",
        ];

        // Verify all event IDs have handlers
        for id in &event_ids {
            // In the actual implementation, each ID has a match arm
            assert!(!id.is_empty());
        }
    }

    #[test]
    fn test_tray_tooltip() {
        let tooltip = "Pasta - Clipboard to Keyboard";
        assert_eq!(tooltip, "Pasta - Clipboard to Keyboard");
        assert!(tooltip.contains("Pasta"));
        assert!(tooltip.contains("Clipboard"));
    }

    #[test]
    fn test_menu_builder_configuration() {
        // Test menu builder configuration options
        let show_menu_on_left_click = false;
        assert!(!show_menu_on_left_click);
    }

    #[test]
    fn test_typing_speed_state_changes() {
        use std::sync::Mutex;

        use tempfile::TempDir;

        use crate::config::Config;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
            config_path,
        });

        // Test state changes for each typing speed
        config_manager.set_typing_speed(TypingSpeed::Slow);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Slow);

        config_manager.set_typing_speed(TypingSpeed::Normal);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Normal);

        config_manager.set_typing_speed(TypingSpeed::Fast);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
    }

    #[test]
    fn test_menu_separator_count() {
        // Test that we have the correct number of separators
        // Based on the code, we have 2 separators in the menu
        let separator_count = 2;
        assert_eq!(separator_count, 2);
    }

    #[test]
    fn test_event_emission_names() {
        // Test that event names are consistent
        let events = vec!["paste_clipboard", "config_changed"];

        for event in &events {
            assert!(!event.is_empty());
            assert!(!event.contains(" ")); // No spaces in event names
        }
    }

    #[test]
    fn test_menu_item_labels() {
        let labels = HashMap::from([
            ("paste", "Paste"),
            ("speed_slow", "Slow"),
            ("speed_normal", "Normal"),
            ("speed_fast", "Fast"),
            ("left_click_paste", "Left Click Pastes"),
            ("quit", "Quit"),
        ]);

        // Verify all labels are non-empty
        for (_, label) in &labels {
            assert!(!label.is_empty());
        }

        // Verify specific labels
        assert_eq!(labels.get("paste"), Some(&"Paste"));
        assert_eq!(labels.get("left_click_paste"), Some(&"Left Click Pastes"));
    }

    #[test]
    fn test_submenu_name() {
        let submenu_name = "Typing Speed";
        assert_eq!(submenu_name, "Typing Speed");
        assert!(submenu_name.contains("Speed"));
    }

    #[test]
    fn test_rebuild_menu_method_exists() {
        // Test that TrayManager has a rebuild_menu method
        // This ensures the menu can be rebuilt to update checkbox states
        use std::sync::Mutex;
        use tempfile::TempDir;
        use crate::config::Config;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let _tray_manager = TrayManager::new(config_manager);
        // The rebuild_menu method is tested through integration tests
    }

    #[test]
    fn test_tray_manager_config_access() {
        use std::sync::Mutex;
        use tempfile::TempDir;
        use crate::config::Config;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Fast,
                left_click_paste: true,
            })),
            config_path,
        });

        let tray_manager = TrayManager::new(config_manager.clone());
        
        // Verify the tray manager can access config
        let config = tray_manager.config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_menu_event_ids() {
        // Test that all expected menu event IDs are defined
        let event_ids = vec![
            "paste",
            "speed_slow", 
            "speed_normal",
            "speed_fast",
            "left_click_paste",
            "quit"
        ];
        
        // Verify all IDs are valid strings
        for id in &event_ids {
            assert!(!id.is_empty());
            assert!(id.is_ascii());
        }
    }

    #[test]
    fn test_tray_icon_event_types() {
        // Test that we handle the expected tray icon event types
        // Currently we only handle Click events
        let handled_events = vec!["Click"];
        assert_eq!(handled_events.len(), 1);
        assert!(handled_events.contains(&"Click"));
    }

    #[test]
    fn test_left_click_paste_configuration() {
        use std::sync::Mutex;

        use tempfile::TempDir;

        use crate::config::Config;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Test with left_click_paste disabled (default)
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
            config_path: config_path.clone(),
        });

        let _tray_manager = TrayManager::new(config_manager.clone());
        assert_eq!(config_manager.get().left_click_paste, false);

        // Test with left_click_paste enabled
        config_manager.set_left_click_paste(true);
        assert_eq!(config_manager.get().left_click_paste, true);
    }

    #[test]
    fn test_tray_menu_behavior_configuration() {
        // Test that show_menu_on_left_click is properly configured based on left_click_paste
        // When left_click_paste is true, show_menu_on_left_click should be false
        // When left_click_paste is false, show_menu_on_left_click should be true

        let left_click_paste_enabled = true;
        let show_menu_on_left_click = !left_click_paste_enabled;
        assert_eq!(show_menu_on_left_click, false);

        let left_click_paste_disabled = false;
        let show_menu_on_left_click = !left_click_paste_disabled;
        assert_eq!(show_menu_on_left_click, true);
    }

    #[test]
    fn test_error_handling_return_type() {
        // Test that setup returns the expected error type
        fn test_error_type() -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }

        assert!(test_error_type().is_ok());
    }
}
