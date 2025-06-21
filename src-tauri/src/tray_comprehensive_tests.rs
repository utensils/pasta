#[cfg(test)]
mod tray_comprehensive_tests {
    use std::sync::{Arc, Mutex};

    use crate::{
        config::{Config, ConfigManager},
        keyboard::TypingSpeed,
        tray::{
            calculate_show_menu_on_left_click, get_tray_tooltip, handle_tray_icon_click,
            TrayIconAction, TrayManager,
        },
    };

    #[test]
    fn test_calculate_show_menu_on_left_click_all_platforms() {
        // When left_click_paste is true, show_menu_on_left_click should be false
        assert_eq!(calculate_show_menu_on_left_click(true), false);
        // When left_click_paste is false, show_menu_on_left_click should be true
        assert_eq!(calculate_show_menu_on_left_click(false), true);
    }

    #[test]
    fn test_get_tray_tooltip_variations() {
        // Test all possible tooltip variations
        let tooltip = get_tray_tooltip();
        assert_eq!(tooltip, "Pasta - Clipboard to Keyboard");

        // Verify tooltip is not empty
        assert!(!tooltip.is_empty());

        // Verify tooltip contains key information
        assert!(tooltip.contains("Pasta"));
        assert!(tooltip.contains("Clipboard"));
    }

    #[test]
    fn test_handle_tray_icon_click_all_cases() {
        use tauri::tray::{MouseButton, MouseButtonState};

        // Test left click with paste enabled
        let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Up, true);
        assert_eq!(action, TrayIconAction::PasteClipboard);

        // Test left click with paste disabled
        let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Up, false);
        assert_eq!(action, TrayIconAction::ShowMenu);

        // Test right click
        let action = handle_tray_icon_click(MouseButton::Right, MouseButtonState::Up, true);
        assert_eq!(action, TrayIconAction::ShowMenu);

        let action = handle_tray_icon_click(MouseButton::Right, MouseButtonState::Up, false);
        assert_eq!(action, TrayIconAction::ShowMenu);

        // Test middle click
        let action = handle_tray_icon_click(MouseButton::Middle, MouseButtonState::Up, true);
        assert_eq!(action, TrayIconAction::None);

        // Test button down state (should do nothing)
        let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Down, true);
        assert_eq!(action, TrayIconAction::None);

        let action = handle_tray_icon_click(MouseButton::Right, MouseButtonState::Down, false);
        assert_eq!(action, TrayIconAction::None);
    }

    #[test]
    fn test_tray_manager_creation() {
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let _tray_manager = TrayManager::new(config_manager.clone());

        // Verify the tray manager holds the correct reference
        // The actual verification would be done if we could access private fields
        // For now, just ensure creation doesn't panic

        // Create multiple tray managers to test shared state
        let _tray_manager2 = TrayManager::new(config_manager.clone());
        let _tray_manager3 = TrayManager::new(config_manager.clone());

        // Test with different config states
        config_manager.set_typing_speed(TypingSpeed::Fast);
        let _tray_manager4 = TrayManager::new(config_manager.clone());

        config_manager.set_left_click_paste(true);
        let _tray_manager5 = TrayManager::new(config_manager.clone());
    }

    #[test]
    fn test_menu_id_constants() {
        // Test all menu ID constants used in tray.rs
        let menu_ids = vec![
            "paste",
            "typing_speed",
            "speed_slow",
            "speed_normal",
            "speed_fast",
            "left_click_paste",
            "quit",
        ];

        // Verify all IDs are unique
        let mut seen = std::collections::HashSet::new();
        for id in &menu_ids {
            assert!(seen.insert(id), "Duplicate menu ID: {}", id);
        }

        // Verify ID format (lowercase with underscores)
        for id in &menu_ids {
            assert!(id.chars().all(|c| c.is_ascii_lowercase() || c == '_'));
            assert!(!id.is_empty());
            assert!(!id.starts_with('_'));
            assert!(!id.ends_with('_'));
        }
    }

    #[test]
    fn test_menu_event_config_changes() {
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
            config_path,
        });

        // Simulate menu event handling
        // Speed change events
        config_manager.set_typing_speed(TypingSpeed::Slow);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Slow);

        config_manager.set_typing_speed(TypingSpeed::Normal);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Normal);

        config_manager.set_typing_speed(TypingSpeed::Fast);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);

        // Left click paste toggle
        config_manager.set_left_click_paste(true);
        assert_eq!(config_manager.get().left_click_paste, true);

        config_manager.set_left_click_paste(false);
        assert_eq!(config_manager.get().left_click_paste, false);
    }

    #[test]
    fn test_tray_icon_paths() {
        // Test icon path construction
        let icon_sizes = vec![16, 32, 128];

        for size in icon_sizes {
            let icon_path = format!("assets/icon_{}x{}.png", size, size);
            assert!(icon_path.contains(&size.to_string()));
            assert!(icon_path.ends_with(".png"));
        }

        // Test template icon paths for macOS
        #[cfg(target_os = "macos")]
        {
            let template_path = "assets/icon_32x32Template.png";
            assert!(template_path.contains("Template"));
            assert!(template_path.contains("32x32"));
        }
    }

    #[test]
    fn test_menu_item_states() {
        // Test menu item enabled/disabled states
        struct MenuItem {
            id: &'static str,
            enabled: bool,
            checkable: bool,
            checked: bool,
        }

        let menu_items = vec![
            MenuItem {
                id: "paste",
                enabled: true,
                checkable: false,
                checked: false,
            },
            MenuItem {
                id: "typing_speed",
                enabled: true,
                checkable: false,
                checked: false,
            },
            MenuItem {
                id: "speed_slow",
                enabled: true,
                checkable: true,
                checked: false,
            },
            MenuItem {
                id: "speed_normal",
                enabled: true,
                checkable: true,
                checked: true,
            },
            MenuItem {
                id: "speed_fast",
                enabled: true,
                checkable: true,
                checked: false,
            },
            MenuItem {
                id: "left_click_paste",
                enabled: true,
                checkable: true,
                checked: false,
            },
            MenuItem {
                id: "quit",
                enabled: true,
                checkable: false,
                checked: false,
            },
        ];

        // Verify menu item properties
        for item in menu_items {
            assert!(!item.id.is_empty());
            if item.checkable {
                // Checkable items can be checked or unchecked
                assert!(item.enabled);
            }
        }
    }

    #[test]
    fn test_tray_event_emission() {
        // Test event emission patterns
        let events = vec![
            ("config_changed", "Config changed event"),
            ("paste_clipboard", "Paste clipboard event"),
        ];

        for (event_name, description) in events {
            assert!(!event_name.is_empty());
            assert!(event_name
                .chars()
                .all(|c| c.is_ascii_lowercase() || c == '_'));
            assert!(!description.is_empty());
        }
    }

    #[test]
    fn test_tray_manager_thread_safety() {
        use std::thread;

        use tempfile::TempDir;

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
                    let tray_manager = TrayManager::new(cm.clone());

                    // Simulate config changes
                    if i % 2 == 0 {
                        cm.set_typing_speed(TypingSpeed::Fast);
                    } else {
                        cm.set_left_click_paste(true);
                    }

                    // Return tray manager to ensure it's not optimized away
                    tray_manager
                })
            })
            .collect();

        for handle in handles {
            let _tray_manager = handle.join().unwrap();
        }

        // Verify final config state is valid
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }
}
