#[cfg(test)]
mod integration_tests {
    use std::{
        path::PathBuf,
        sync::{Arc, Mutex},
    };

    use tempfile::TempDir;

    use crate::{
        app_logic::{handle_paste_clipboard, ClipboardProvider},
        config::{Config, ConfigManager},
        create_app_state, handle_config_changed, handle_paste_clipboard_event,
        initialize_components,
        keyboard::{KeyboardEmulator, TypingSpeed},
        tray::TrayManager,
    };

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_full_app_initialization_flow() {
        // Test complete initialization sequence
        let result = initialize_components();
        assert!(result.is_ok());

        let (config_manager, keyboard_emulator) = result.unwrap();

        // Verify components are properly connected
        let config = config_manager.get();
        keyboard_emulator.set_typing_speed(config.typing_speed);

        // Create app state
        let app_state = create_app_state(keyboard_emulator.clone());

        // Verify state is valid
        assert!(Arc::strong_count(&app_state.keyboard_emulator) > 1);

        // Create tray manager
        let _tray_manager = TrayManager::new(config_manager.clone());

        // Full initialization complete
    }

    #[test]
    fn test_config_persistence_integration() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Create first instance
        {
            let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
            config_manager.set_typing_speed(TypingSpeed::Fast);
            config_manager.set_left_click_paste(true);
        }

        // Create second instance - should load persisted config
        {
            let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
            let config = config_manager.get();
            assert_eq!(config.typing_speed, TypingSpeed::Fast);
            assert_eq!(config.left_click_paste, true);
        }
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_keyboard_config_sync() {
        // Test that keyboard emulator stays in sync with config
        let (config_manager, keyboard_emulator) = initialize_components().unwrap();

        // Change config multiple times
        for speed in &[TypingSpeed::Slow, TypingSpeed::Fast, TypingSpeed::Normal] {
            config_manager.set_typing_speed(*speed);
            handle_config_changed(&config_manager, &keyboard_emulator);

            // Verify config is applied
            assert_eq!(config_manager.get().typing_speed, *speed);
        }
    }

    #[tokio::test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    async fn test_paste_operation_flow() {
        // Test complete paste operation flow
        struct MockClipboard {
            content: Option<String>,
        }

        impl ClipboardProvider for MockClipboard {
            fn get_content(&self) -> Result<Option<String>, String> {
                Ok(self.content.clone())
            }
        }

        let clipboard = MockClipboard {
            content: Some("Test content".to_string()),
        };

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Execute paste operation
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_ok());
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_event_handler_integration() {
        // Note: tauri::test is not available in v2, so we test the logic directly

        let (config_manager, keyboard_emulator) = initialize_components().unwrap();

        // Test event handling logic directly without Tauri app instance

        // Change config and verify handler logic works
        config_manager.set_typing_speed(TypingSpeed::Fast);
        handle_config_changed(&config_manager, &keyboard_emulator);

        // Verify config was applied
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);

        // Test paste event
        handle_paste_clipboard_event(keyboard_emulator.clone());

        std::thread::sleep(std::time::Duration::from_millis(50));
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_concurrent_operations() {
        use std::thread;

        let (config_manager, keyboard_emulator) = initialize_components().unwrap();

        let handles: Vec<_> = (0..10)
            .map(|i| {
                let cm = config_manager.clone();
                let ke = keyboard_emulator.clone();

                thread::spawn(move || {
                    if i % 2 == 0 {
                        // Config changes
                        let speed = match i % 6 {
                            0 => TypingSpeed::Slow,
                            2 => TypingSpeed::Normal,
                            _ => TypingSpeed::Fast,
                        };
                        cm.set_typing_speed(speed);
                        handle_config_changed(&cm, &ke);
                    } else {
                        // Paste operations
                        handle_paste_clipboard_event(ke);
                    }
                })
            })
            .collect();

        for handle in handles {
            handle.join().unwrap();
        }

        // Verify system is still in valid state
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }

    #[test]
    fn test_error_propagation() {
        // Test error handling throughout the system

        // Test with invalid config path
        let invalid_path = PathBuf::from("/root/no/permission/config.toml");
        let result = ConfigManager::new_with_path(invalid_path);

        // Should handle gracefully (creates default config in memory)
        assert!(result.is_ok());
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_state_consistency() {
        // Test that state remains consistent across operations
        let (config_manager, keyboard_emulator) = initialize_components().unwrap();
        let app_state = create_app_state(keyboard_emulator.clone());

        // Perform various operations
        config_manager.set_typing_speed(TypingSpeed::Fast);
        config_manager.set_left_click_paste(true);

        handle_config_changed(&config_manager, &keyboard_emulator);

        // Clone state multiple times
        let state1 = app_state.clone();
        let state2 = app_state.clone();

        // Verify all clones share same keyboard emulator
        assert!(Arc::ptr_eq(
            &state1.keyboard_emulator,
            &state2.keyboard_emulator
        ));
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &keyboard_emulator
        ));
    }

    #[test]
    fn test_menu_event_flow() {
        use crate::app_logic::handle_menu_event;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        // Test menu events
        let events = vec![
            "paste",
            "speed_slow",
            "speed_normal",
            "speed_fast",
            "left_click_paste",
            "quit",
        ];

        for event_id in events {
            let action = handle_menu_event(event_id);

            // Handle menu actions
            match action {
                crate::app_logic::MenuAction::SetTypingSpeed(speed) => {
                    config_manager.set_typing_speed(speed);

                    // Verify config was updated
                    let config = config_manager.get();
                    assert_eq!(config.typing_speed, speed);
                }
                crate::app_logic::MenuAction::ToggleLeftClickPaste => {
                    let old_value = config_manager.get().left_click_paste;
                    config_manager.set_left_click_paste(!old_value);
                }
                _ => {}
            }
        }
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_clipboard_keyboard_integration() {
        // Test clipboard to keyboard data flow
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Test with various content types
        let long_text = "Very long text ".repeat(100);
        let test_contents = vec![
            "Simple text",
            "Multi\nline\ntext",
            "Text with\ttabs",
            "Unicode: 🦀 café",
            long_text.as_str(),
        ];

        let runtime = tokio::runtime::Runtime::new().unwrap();

        for content in test_contents {
            runtime.block_on(async {
                let result = keyboard_emulator.type_text(content).await;
                assert!(result.is_ok());
            });
        }
    }

    #[test]
    #[ignore = "Uses real KeyboardEmulator which types on the system"]
    fn test_shutdown_sequence() {
        // Test graceful shutdown
        let (config_manager, keyboard_emulator) = initialize_components().unwrap();
        let app_state = create_app_state(keyboard_emulator.clone());

        // Simulate app shutdown by dropping components
        drop(app_state);

        // Config manager should still work
        config_manager.set_typing_speed(TypingSpeed::Slow);
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Slow);

        // Drop remaining components
        drop(keyboard_emulator);
        drop(config_manager);
    }

    #[test]
    fn test_startup_delay_behavior() {
        use std::time::{Duration, Instant};

        use crate::helpers::get_startup_delay;

        let start = Instant::now();
        let delay = get_startup_delay();
        std::thread::sleep(delay);
        let elapsed = start.elapsed();

        // Verify delay is applied correctly
        assert!(elapsed >= delay);
        assert!(elapsed < delay + Duration::from_millis(50)); // Allow some tolerance
    }
}
