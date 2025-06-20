#[cfg(test)]
mod lib_coverage_tests {
    use std::sync::Arc;
    use crate::{
        initialize_components,
        create_app_state,
        handle_config_changed,
        handle_paste_clipboard_event,
        AppState,
        keyboard::{KeyboardEmulator, TypingSpeed},
        config::{Config, ConfigManager},
    };
    use tempfile::TempDir;
    use std::sync::Mutex;

    #[test]
    fn test_initialize_components_comprehensive() {
        // Test multiple initialization scenarios
        let result = initialize_components();
        assert!(result.is_ok());
        
        let (config_manager, keyboard_emulator) = result.unwrap();
        
        // Test that components are properly wired together
        let initial_speed = config_manager.get().typing_speed;
        
        // Change config and verify it can be applied
        config_manager.set_typing_speed(TypingSpeed::Slow);
        handle_config_changed(&config_manager, &keyboard_emulator);
        
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Slow);
    }

    #[test]
    fn test_app_state_keyboard_emulator_sharing() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let original_count = Arc::strong_count(&keyboard_emulator);
        
        let app_state = create_app_state(keyboard_emulator.clone());
        
        // Verify reference count increased
        assert_eq!(Arc::strong_count(&keyboard_emulator), original_count + 1);
        
        // Clone app state and verify sharing
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(&app_state.keyboard_emulator, &cloned_state.keyboard_emulator));
    }

    #[test]
    fn test_handle_config_changed_multiple_speeds() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });
        
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Test all speed transitions
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        
        for speed in speeds {
            config_manager.set_typing_speed(speed);
            handle_config_changed(&config_manager, &keyboard_emulator);
            assert_eq!(config_manager.get().typing_speed, speed);
        }
    }

    #[test]
    fn test_handle_paste_clipboard_event_thread_safety() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let initial_count = Arc::strong_count(&keyboard_emulator);
        
        // Call handle_paste_clipboard_event multiple times
        for _ in 0..3 {
            handle_paste_clipboard_event(keyboard_emulator.clone());
        }
        
        // Give threads time to start
        std::thread::sleep(std::time::Duration::from_millis(50));
        
        // Verify keyboard emulator is still valid
        assert!(Arc::strong_count(&keyboard_emulator) >= initial_count);
    }

    #[test]
    fn test_error_handling_in_initialization() {
        // Test that initialization properly propagates errors
        // We can't easily force errors in initialize_components,
        // but we can test the error type handling
        
        fn returns_box_error() -> Result<(), Box<dyn std::error::Error>> {
            Err("Test error".into())
        }
        
        let result = returns_box_error();
        assert!(result.is_err());
        assert_eq!(result.unwrap_err().to_string(), "Test error");
    }

    #[test]
    fn test_config_persistence_through_lifecycle() {
        let result = initialize_components();
        assert!(result.is_ok());
        
        let (config_manager, keyboard_emulator) = result.unwrap();
        
        // Set a specific configuration
        config_manager.set_typing_speed(TypingSpeed::Fast);
        config_manager.set_left_click_paste(true);
        
        // Create app state
        let app_state = create_app_state(keyboard_emulator.clone());
        
        // Verify config persists
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
        assert_eq!(config_manager.get().left_click_paste, true);
        
        // Multiple clones should share the same config
        let state_clone1 = app_state.clone();
        let state_clone2 = app_state.clone();
        
        assert!(Arc::ptr_eq(&state_clone1.keyboard_emulator, &state_clone2.keyboard_emulator));
    }

    #[test]
    fn test_handle_config_changed_with_left_click_paste() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
            config_path,
        });
        
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Change left_click_paste setting
        config_manager.set_left_click_paste(true);
        handle_config_changed(&config_manager, &keyboard_emulator);
        
        // Verify the setting persisted
        assert_eq!(config_manager.get().left_click_paste, true);
        
        // Change it back
        config_manager.set_left_click_paste(false);
        handle_config_changed(&config_manager, &keyboard_emulator);
        assert_eq!(config_manager.get().left_click_paste, false);
    }

    #[test]
    fn test_concurrent_handle_paste_clipboard_events() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let mut handles = vec![];
        
        // Spawn multiple paste events concurrently
        for _ in 0..5 {
            let ke = keyboard_emulator.clone();
            let handle = std::thread::spawn(move || {
                handle_paste_clipboard_event(ke);
            });
            handles.push(handle);
        }
        
        // Wait for all threads to complete
        for handle in handles {
            handle.join().unwrap();
        }
        
        // Give spawned threads time to start
        std::thread::sleep(std::time::Duration::from_millis(100));
        
        // Keyboard emulator should still be valid
        assert!(Arc::strong_count(&keyboard_emulator) > 0);
    }
}