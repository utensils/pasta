#[cfg(test)]
mod comprehensive_integration_tests {
    

    

    use crate::{
        app_logic::{
            create_menu_structure, handle_menu_event, MenuAction, MenuItem,
        },
        create_app_state, handle_config_changed, handle_paste_clipboard_event,
        initialize_components,
        keyboard::TypingSpeed,
        tray::{
            calculate_show_menu_on_left_click, get_tray_tooltip, handle_tray_icon_click,
            TrayIconAction,
        },
    };

    #[test]
    fn test_full_application_flow() {
        // Test a complete application flow from initialization to usage

        // 1. Initialize components
        let result = initialize_components();
        assert!(result.is_ok());
        let (config_manager, keyboard_emulator) = result.unwrap();

        // 2. Create app state
        let _app_state = create_app_state(keyboard_emulator.clone());

        // 3. Test configuration changes
        config_manager.set_typing_speed(TypingSpeed::Fast);
        config_manager.set_left_click_paste(true);
        handle_config_changed(&config_manager, &keyboard_emulator);

        // 4. Verify settings persisted
        let config = config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, true);

        // 5. Test menu structure creation
        let menu_structure = create_menu_structure(config.typing_speed, config.left_click_paste);
        assert_eq!(menu_structure.items.len(), 6); // Expected number of menu items

        // 6. Test menu event handling
        let paste_action = handle_menu_event("paste");
        assert_eq!(paste_action, MenuAction::Paste);

        // 7. Test tray icon behavior
        let tray_action = handle_tray_icon_click(
            tauri::tray::MouseButton::Left,
            tauri::tray::MouseButtonState::Up,
            config.left_click_paste,
        );
        assert_eq!(tray_action, TrayIconAction::PasteClipboard);

        // 8. Test paste event handling
        handle_paste_clipboard_event(keyboard_emulator.clone());
    }

    #[test]
    fn test_all_menu_configurations() {
        // Test all possible menu configurations
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let left_click_options = vec![true, false];

        for speed in speeds {
            for &left_click in &left_click_options {
                let menu = create_menu_structure(speed, left_click);

                // Verify menu has expected structure
                assert!(menu.items.len() > 0);

                // Find typing speed submenu
                let has_speed_submenu = menu.items.iter().any(|item| {
                    matches!(item, MenuItem::Submenu { label, .. } if label == "Typing Speed")
                });
                assert!(has_speed_submenu);

                // Find left click paste item
                let has_left_click_item = menu.items.iter().any(|item| {
                    matches!(item, MenuItem::CheckItem { id, checked, .. } 
                        if id == "left_click_paste" && *checked == left_click)
                });
                assert!(has_left_click_item);
            }
        }
    }

    #[test]
    fn test_all_tray_icon_interactions() {
        use tauri::tray::{MouseButton, MouseButtonState};

        // Test all possible tray icon interactions
        let buttons = vec![MouseButton::Left, MouseButton::Right, MouseButton::Middle];

        let states = vec![MouseButtonState::Up, MouseButtonState::Down];

        let left_click_paste_options = vec![true, false];

        for button in &buttons {
            for state in &states {
                for &left_click_paste in &left_click_paste_options {
                    let action = handle_tray_icon_click(*button, *state, left_click_paste);

                    // Verify expected behavior
                    match (button, state, left_click_paste) {
                        (MouseButton::Left, MouseButtonState::Up, true) => {
                            assert_eq!(action, TrayIconAction::PasteClipboard);
                        }
                        (MouseButton::Left, MouseButtonState::Up, false) => {
                            assert_eq!(action, TrayIconAction::ShowMenu);
                        }
                        (MouseButton::Right, MouseButtonState::Up, _) => {
                            assert_eq!(action, TrayIconAction::ShowMenu);
                        }
                        _ => {
                            assert_eq!(action, TrayIconAction::None);
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn test_concurrent_operations() {
        use std::{thread, time::Duration};

        let result = initialize_components();
        assert!(result.is_ok());
        let (config_manager, keyboard_emulator) = result.unwrap();

        let mut handles = vec![];

        // Spawn config readers
        for _ in 0..5 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for _ in 0..50 {
                    let _config = cm.get();
                    thread::sleep(Duration::from_micros(100));
                }
            }));
        }

        // Spawn config writers
        for i in 0..3 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for j in 0..30 {
                    if (i + j) % 2 == 0 {
                        cm.set_typing_speed(TypingSpeed::Fast);
                    } else {
                        cm.set_left_click_paste(true);
                    }
                    thread::sleep(Duration::from_micros(150));
                }
            }));
        }

        // Spawn paste event handlers
        for _ in 0..2 {
            let ke = keyboard_emulator.clone();
            handles.push(thread::spawn(move || {
                for _ in 0..10 {
                    handle_paste_clipboard_event(ke.clone());
                    thread::sleep(Duration::from_millis(5));
                }
            }));
        }

        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }
    }

    #[test]
    fn test_menu_structure_consistency() {
        // Ensure menu structure is consistent across different states
        let menu1 = create_menu_structure(TypingSpeed::Normal, false);
        let menu2 = create_menu_structure(TypingSpeed::Normal, false);

        // Should produce identical structures
        assert_eq!(menu1.items.len(), menu2.items.len());

        // Test that changing only one parameter changes the structure appropriately
        let menu3 = create_menu_structure(TypingSpeed::Fast, false);
        assert_eq!(menu1.items.len(), menu3.items.len()); // Same number of items

        let menu4 = create_menu_structure(TypingSpeed::Normal, true);
        assert_eq!(menu1.items.len(), menu4.items.len()); // Same number of items
    }

    #[test]
    fn test_tray_tooltip_consistency() {
        // Tooltip should always be the same
        let tooltip1 = get_tray_tooltip();
        let tooltip2 = get_tray_tooltip();
        assert_eq!(tooltip1, tooltip2);
        assert_eq!(tooltip1, "Pasta - Clipboard to Keyboard");
    }

    #[test]
    fn test_show_menu_calculation() {
        // Test the logic for when to show menu on left click
        assert_eq!(calculate_show_menu_on_left_click(true), false);
        assert_eq!(calculate_show_menu_on_left_click(false), true);

        // Test with various boolean values
        for &value in &[true, false] {
            let result = calculate_show_menu_on_left_click(value);
            assert_eq!(result, !value);
        }
    }
}
