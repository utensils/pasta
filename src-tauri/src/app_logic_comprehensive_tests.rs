#[cfg(test)]
mod app_logic_comprehensive_tests {
    use std::sync::{Arc, Mutex};

    

    use crate::{
        app_logic::{
            create_menu_structure, handle_menu_event, handle_paste_clipboard, ClipboardProvider,
            MenuAction, MenuItem, SystemClipboard,
        },
        keyboard::{KeyboardEmulator, TypingSpeed},
    };

    // Comprehensive mock clipboard for testing
    struct MockClipboard {
        content: Result<Option<String>, String>,
        call_count: Arc<Mutex<usize>>,
    }

    impl MockClipboard {
        fn new(content: Result<Option<String>, String>) -> Self {
            Self {
                content,
                call_count: Arc::new(Mutex::new(0)),
            }
        }

        fn get_call_count(&self) -> usize {
            *self.call_count.lock().unwrap()
        }
    }

    impl ClipboardProvider for MockClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            *self.call_count.lock().unwrap() += 1;
            self.content.clone()
        }
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    async fn test_handle_paste_clipboard_all_scenarios() {
        let keyboard = Arc::new(KeyboardEmulator::new().unwrap());

        // Test successful paste
        let clipboard = MockClipboard::new(Ok(Some("Hello World".to_string())));
        let result = handle_paste_clipboard(&clipboard, &keyboard).await;
        assert!(result.is_ok());
        assert_eq!(clipboard.get_call_count(), 1);

        // Test empty clipboard
        let empty_clipboard = MockClipboard::new(Ok(None));
        let result = handle_paste_clipboard(&empty_clipboard, &keyboard).await;
        assert!(result.is_ok()); // Empty clipboard now returns Ok

        // Test clipboard error
        let error_clipboard = MockClipboard::new(Err("Access denied".to_string()));
        let result = handle_paste_clipboard(&error_clipboard, &keyboard).await;
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Access denied");

        // Test very long content
        let long_content = "x".repeat(10000);
        let long_clipboard = MockClipboard::new(Ok(Some(long_content)));
        let result = handle_paste_clipboard(&long_clipboard, &keyboard).await;
        assert!(result.is_ok());

        // Test unicode content
        let unicode_clipboard = MockClipboard::new(Ok(Some("Hello 世界 🦀".to_string())));
        let result = handle_paste_clipboard(&unicode_clipboard, &keyboard).await;
        assert!(result.is_ok());

        // Test content with special characters
        let special_clipboard = MockClipboard::new(Ok(Some("Line1\nLine2\tTab".to_string())));
        let result = handle_paste_clipboard(&special_clipboard, &keyboard).await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_create_menu_structure_comprehensive() {
        // Test with different initial configs
        let typing_speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let left_click_states = vec![true, false];

        for typing_speed in typing_speeds {
            for left_click_paste in &left_click_states {
                let menu_structure = create_menu_structure(typing_speed, *left_click_paste);

                // Verify menu structure
                assert_eq!(menu_structure.items.len(), 6); // paste, separator, typing_speed, left_click_paste, separator, quit

                // Verify paste item
                match &menu_structure.items[0] {
                    MenuItem::Action { id, label } => {
                        assert_eq!(id, "paste");
                        assert_eq!(label, "Paste");
                    }
                    _ => panic!("Expected Action item"),
                }

                // Verify separator
                assert!(matches!(menu_structure.items[1], MenuItem::Separator));

                // Verify typing speed submenu
                match &menu_structure.items[2] {
                    MenuItem::Submenu { label, .. } => {
                        assert_eq!(label, "Typing Speed");
                    }
                    _ => panic!("Expected Submenu"),
                }

                // Check submenu items
                if let MenuItem::Submenu { items, .. } = &menu_structure.items[2] {
                    assert_eq!(items.len(), 3);

                    // Check which speed is selected
                    for item in items {
                        if let MenuItem::CheckItem { id, checked, .. } = item {
                            match (id.as_str(), typing_speed) {
                                ("speed_slow", TypingSpeed::Slow) => assert!(*checked),
                                ("speed_normal", TypingSpeed::Normal) => assert!(*checked),
                                ("speed_fast", TypingSpeed::Fast) => assert!(*checked),
                                _ => assert!(!checked),
                            }
                        }
                    }
                }

                // Verify left click paste item
                match &menu_structure.items[3] {
                    MenuItem::CheckItem { id, label, checked } => {
                        assert_eq!(id, "left_click_paste");
                        assert_eq!(label, "Left Click Pastes");
                        assert_eq!(*checked, *left_click_paste);
                    }
                    _ => panic!("Expected CheckItem"),
                }

                // Verify separator
                assert!(matches!(menu_structure.items[4], MenuItem::Separator));

                // Verify quit item
                match &menu_structure.items[5] {
                    MenuItem::Action { id, label } => {
                        assert_eq!(id, "quit");
                        assert_eq!(label, "Quit");
                    }
                    _ => panic!("Expected Action item"),
                }
            }
        }
    }

    #[test]
    fn test_handle_menu_event_all_events() {
        // Test paste event
        let action = handle_menu_event("paste");
        assert_eq!(action, MenuAction::Paste);

        // Test speed events
        let action = handle_menu_event("speed_slow");
        assert_eq!(action, MenuAction::SetTypingSpeed(TypingSpeed::Slow));

        let action = handle_menu_event("speed_normal");
        assert_eq!(action, MenuAction::SetTypingSpeed(TypingSpeed::Normal));

        let action = handle_menu_event("speed_fast");
        assert_eq!(action, MenuAction::SetTypingSpeed(TypingSpeed::Fast));

        // Test left click paste toggle
        let action = handle_menu_event("left_click_paste");
        assert_eq!(action, MenuAction::ToggleLeftClickPaste);

        // Test quit event
        let action = handle_menu_event("quit");
        assert_eq!(action, MenuAction::Quit);

        // Test unknown event
        let action = handle_menu_event("unknown_event");
        assert_eq!(action, MenuAction::None);
    }

    #[test]
    fn test_system_clipboard_wrapper() {
        // Test SystemClipboard implementation
        let clipboard = SystemClipboard;

        // We can't test the actual clipboard access without system dependency,
        // but we can verify the method exists and returns the correct type
        let result = clipboard.get_content();

        // Result should be of correct type
        match result {
            Ok(Some(content)) => {
                // Content is a string
                let _: String = content;
            }
            Ok(None) => {
                // Empty clipboard
            }
            Err(error) => {
                // Error is a string
                let _: String = error;
            }
        }
    }

    #[test]
    fn test_menu_structure_consistency() {
        // Create menu multiple times and verify consistency
        for _ in 0..5 {
            let menu_structure1 = create_menu_structure(TypingSpeed::Normal, false);
            let menu_structure2 = create_menu_structure(TypingSpeed::Normal, false);

            // Menu structure should be identical
            assert_eq!(menu_structure1.items.len(), menu_structure2.items.len());

            // All items should match
            for (item1, item2) in menu_structure1
                .items
                .iter()
                .zip(menu_structure2.items.iter())
            {
                match (item1, item2) {
                    (MenuItem::Action { id: id1, .. }, MenuItem::Action { id: id2, .. }) => {
                        assert_eq!(id1, id2);
                    }
                    (MenuItem::CheckItem { id: id1, .. }, MenuItem::CheckItem { id: id2, .. }) => {
                        assert_eq!(id1, id2);
                    }
                    (MenuItem::Submenu { label: l1, .. }, MenuItem::Submenu { label: l2, .. }) => {
                        assert_eq!(l1, l2);
                    }
                    (MenuItem::Separator, MenuItem::Separator) => {}
                    _ => panic!("Mismatched item types"),
                }
            }
        }
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    async fn test_paste_clipboard_error_messages() {
        let keyboard = Arc::new(KeyboardEmulator::new().unwrap());

        // Test specific error messages
        let error_scenarios = vec![
            (Err("Permission denied".to_string()), "Permission denied"),
            (Err("Clipboard locked".to_string()), "Clipboard locked"),
            (Err("Unknown error".to_string()), "Unknown error"),
        ];

        for (clipboard_result, expected_error) in error_scenarios {
            let clipboard = MockClipboard::new(clipboard_result);
            let result = handle_paste_clipboard(&clipboard, &keyboard).await;

            assert!(result.is_err());
            assert_eq!(result.unwrap_err(), expected_error);
        }
    }

    #[test]
    fn test_menu_action_equality() {
        // Test MenuAction equality
        assert_eq!(MenuAction::Paste, MenuAction::Paste);
        assert_eq!(
            MenuAction::SetTypingSpeed(TypingSpeed::Fast),
            MenuAction::SetTypingSpeed(TypingSpeed::Fast)
        );
        assert_ne!(
            MenuAction::SetTypingSpeed(TypingSpeed::Fast),
            MenuAction::SetTypingSpeed(TypingSpeed::Slow)
        );
        assert_eq!(
            MenuAction::ToggleLeftClickPaste,
            MenuAction::ToggleLeftClickPaste
        );
        assert_eq!(MenuAction::Quit, MenuAction::Quit);
        assert_eq!(MenuAction::None, MenuAction::None);
    }

    #[test]
    fn test_menu_structure_with_different_states() {
        // Test menu creation with all combinations
        let states = vec![
            (TypingSpeed::Slow, true),
            (TypingSpeed::Slow, false),
            (TypingSpeed::Normal, true),
            (TypingSpeed::Normal, false),
            (TypingSpeed::Fast, true),
            (TypingSpeed::Fast, false),
        ];

        for (speed, left_click) in states {
            let menu = create_menu_structure(speed, left_click);
            assert_eq!(menu.items.len(), 6); // paste, sep, speed, left_click, sep, quit

            // Verify correct speed is selected
            if let MenuItem::Submenu { items, .. } = &menu.items[2] {
                let checked_count = items
                    .iter()
                    .filter(|item| {
                        if let MenuItem::CheckItem { checked, .. } = item {
                            *checked
                        } else {
                            false
                        }
                    })
                    .count();
                assert_eq!(checked_count, 1); // Exactly one speed should be selected
            }
        }
    }
}
