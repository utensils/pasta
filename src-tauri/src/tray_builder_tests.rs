#[cfg(test)]
mod tray_builder_tests {
    use std::sync::{Arc, Mutex};

    use tempfile::TempDir;

    use crate::{
        app_logic::{
            create_menu_structure, handle_menu_event, MenuAction, MenuItem, MenuStructure,
        },
        config::{Config, ConfigManager},
        keyboard::TypingSpeed,
        tray::{calculate_show_menu_on_left_click, get_tray_tooltip, TrayManager},
    };

    // Helper function to create test config manager
    fn create_test_config_manager(
        typing_speed: TypingSpeed,
        left_click_paste: bool,
    ) -> Arc<ConfigManager> {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed,
                left_click_paste,
            })),
            config_path,
        })
    }

    #[test]
    fn test_menu_structure_to_tauri_conversion_logic() {
        // Test the conversion logic from MenuStructure to Tauri menu items
        // This tests the structure that build_tauri_menu would create

        let menu_structure = create_menu_structure(TypingSpeed::Normal, false);

        // Verify the structure has all expected items
        let mut action_count = 0;
        let mut check_count = 0;
        let mut submenu_count = 0;
        let mut separator_count = 0;

        for item in &menu_structure.items {
            match item {
                MenuItem::Action { .. } => action_count += 1,
                MenuItem::CheckItem { .. } => check_count += 1,
                MenuItem::Submenu { .. } => submenu_count += 1,
                MenuItem::Separator => separator_count += 1,
            }
        }

        assert_eq!(action_count, 3); // Paste, Cancel Typing, Quit
        assert_eq!(check_count, 1); // Left Click Pastes
        assert_eq!(submenu_count, 1); // Typing Speed
        assert_eq!(separator_count, 2); // Two separators
    }

    #[test]
    fn test_submenu_structure_conversion() {
        // Test submenu structure conversion
        let menu_structure = create_menu_structure(TypingSpeed::Fast, true);

        // Find the typing speed submenu
        let typing_speed_submenu = menu_structure.items.iter().find_map(|item| {
            if let MenuItem::Submenu { label, items } = item {
                if label == "Typing Speed" {
                    Some(items)
                } else {
                    None
                }
            } else {
                None
            }
        });

        assert!(typing_speed_submenu.is_some());
        let submenu_items = typing_speed_submenu.unwrap();

        // Verify submenu has exactly 3 speed options
        assert_eq!(submenu_items.len(), 3);

        // Verify only one is checked (Fast)
        let checked_items: Vec<_> = submenu_items
            .iter()
            .filter_map(|item| {
                if let MenuItem::CheckItem { id, checked, .. } = item {
                    if *checked {
                        Some(id.as_str())
                    } else {
                        None
                    }
                } else {
                    None
                }
            })
            .collect();

        assert_eq!(checked_items.len(), 1);
        assert_eq!(checked_items[0], "speed_fast");
    }

    #[test]
    fn test_menu_event_handling_flow() {
        // Test the flow of menu event handling
        let config_manager = create_test_config_manager(TypingSpeed::Normal, false);
        let _tray_manager = TrayManager::new(config_manager.clone());

        // Simulate menu events
        let events = vec![
            ("paste", MenuAction::Paste),
            ("speed_slow", MenuAction::SetTypingSpeed(TypingSpeed::Slow)),
            (
                "speed_normal",
                MenuAction::SetTypingSpeed(TypingSpeed::Normal),
            ),
            ("speed_fast", MenuAction::SetTypingSpeed(TypingSpeed::Fast)),
            ("left_click_paste", MenuAction::ToggleLeftClickPaste),
            ("quit", MenuAction::Quit),
            ("unknown", MenuAction::None),
        ];

        for (event_id, expected_action) in events {
            let action = handle_menu_event(event_id);
            assert_eq!(action, expected_action);
        }
    }

    #[test]
    fn test_tray_behavior_updates() {
        // Test tray behavior updates when config changes
        let config_manager = create_test_config_manager(TypingSpeed::Normal, false);

        // Initially, left_click_paste is false, so show_menu_on_left_click should be true
        assert_eq!(calculate_show_menu_on_left_click(false), true);

        // After toggling
        config_manager.set_left_click_paste(true);
        assert_eq!(calculate_show_menu_on_left_click(true), false);
    }

    #[test]
    fn test_menu_rebuild_scenarios() {
        // Test scenarios where menu needs to be rebuilt
        let config_manager = create_test_config_manager(TypingSpeed::Normal, false);
        let initial_config = config_manager.get();

        // Scenario 1: Typing speed change
        config_manager.set_typing_speed(TypingSpeed::Fast);
        let config_after_speed = config_manager.get();
        assert_ne!(initial_config.typing_speed, config_after_speed.typing_speed);

        // Verify the menu structure would be different
        let menu1 =
            create_menu_structure(initial_config.typing_speed, initial_config.left_click_paste);
        let menu2 = create_menu_structure(
            config_after_speed.typing_speed,
            config_after_speed.left_click_paste,
        );

        // Find which speed item is checked in each menu
        let get_checked_speed = |menu: &MenuStructure| -> Option<String> {
            menu.items.iter().find_map(|item| {
                if let MenuItem::Submenu { items, .. } = item {
                    items.iter().find_map(|sub_item| {
                        if let MenuItem::CheckItem { id, checked, .. } = sub_item {
                            if *checked {
                                Some(id.clone())
                            } else {
                                None
                            }
                        } else {
                            None
                        }
                    })
                } else {
                    None
                }
            })
        };

        assert_eq!(get_checked_speed(&menu1), Some("speed_normal".to_string()));
        assert_eq!(get_checked_speed(&menu2), Some("speed_fast".to_string()));

        // Scenario 2: Left click paste toggle
        config_manager.set_left_click_paste(true);
        let config_after_toggle = config_manager.get();
        assert_ne!(
            initial_config.left_click_paste,
            config_after_toggle.left_click_paste
        );
    }

    #[test]
    fn test_menu_item_id_stability() {
        // Test that menu item IDs remain stable across rebuilds
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let left_click_options = vec![true, false];

        let mut all_ids = std::collections::HashSet::new();

        for speed in &speeds {
            for &left_click in &left_click_options {
                let menu = create_menu_structure(*speed, left_click);

                // Collect all IDs from this menu configuration
                for item in &menu.items {
                    match item {
                        MenuItem::Action { id, .. } => {
                            all_ids.insert(id.clone());
                        }
                        MenuItem::CheckItem { id, .. } => {
                            all_ids.insert(id.clone());
                        }
                        MenuItem::Submenu { items, .. } => {
                            for sub_item in items {
                                if let MenuItem::CheckItem { id, .. } = sub_item {
                                    all_ids.insert(id.clone());
                                }
                            }
                        }
                        MenuItem::Separator => {}
                    }
                }
            }
        }

        // Verify expected IDs are present
        assert!(all_ids.contains("paste"));
        assert!(all_ids.contains("speed_slow"));
        assert!(all_ids.contains("speed_normal"));
        assert!(all_ids.contains("speed_fast"));
        assert!(all_ids.contains("left_click_paste"));
        assert!(all_ids.contains("quit"));
    }

    #[test]
    fn test_tooltip_consistency_across_configs() {
        // Tooltip should remain the same regardless of config
        let configs = vec![
            (TypingSpeed::Slow, true),
            (TypingSpeed::Normal, false),
            (TypingSpeed::Fast, true),
        ];

        for (speed, left_click) in configs {
            let _config_manager = create_test_config_manager(speed, left_click);
            let tooltip = get_tray_tooltip();
            assert_eq!(tooltip, "Pasta - Clipboard to Keyboard");
        }
    }

    #[test]
    fn test_menu_structure_edge_cases() {
        // Test edge cases in menu structure

        // Test with all combinations to ensure no panics
        let all_speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let all_bools = vec![true, false];

        for speed in &all_speeds {
            for &left_click in &all_bools {
                let menu = create_menu_structure(*speed, left_click);

                // Verify menu is never empty
                assert!(!menu.items.is_empty());

                // Verify there's always a paste item
                let has_paste = menu
                    .items
                    .iter()
                    .any(|item| matches!(item, MenuItem::Action { id, .. } if id == "paste"));
                assert!(has_paste);

                // Verify there's always a quit item
                let has_quit = menu
                    .items
                    .iter()
                    .any(|item| matches!(item, MenuItem::Action { id, .. } if id == "quit"));
                assert!(has_quit);
            }
        }
    }

    #[test]
    fn test_concurrent_menu_operations() {
        use std::{thread, time::Duration};

        let config_manager = create_test_config_manager(TypingSpeed::Normal, false);

        let mut handles = vec![];

        // Simulate concurrent menu operations
        for i in 0..5 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for j in 0..10 {
                    let speed = match (i + j) % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };
                    cm.set_typing_speed(speed);

                    // Simulate menu rebuild by creating menu structure
                    let config = cm.get();
                    let _menu = create_menu_structure(config.typing_speed, config.left_click_paste);

                    thread::sleep(Duration::from_micros(100));
                }
            }));
        }

        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }

        // Verify config is still valid
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }
}
