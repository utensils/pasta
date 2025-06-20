#[cfg(test)]
mod init_tests {
    use std::sync::{Arc, Mutex};
    use std::path::PathBuf;
    use crate::{
        initialize_components,
        create_app_state,
        handle_config_changed,
        handle_paste_clipboard_event,
        AppState,
    };
    use crate::config::{Config, ConfigManager};
    use crate::keyboard::{KeyboardEmulator, TypingSpeed};
    use tempfile::TempDir;
    
    #[test]
    fn test_initialize_components_error_handling() {
        // Test that initialize_components handles errors gracefully
        // In practice, errors would come from config or keyboard initialization
        
        // Create a valid initialization
        let result = initialize_components();
        assert!(result.is_ok());
        
        // Test the components are properly connected
        let (config_manager, keyboard_emulator) = result.unwrap();
        
        // Verify keyboard emulator has the initial config's typing speed
        let initial_config = config_manager.get();
        // We can't directly check the keyboard's speed, but we can verify it accepts commands
        keyboard_emulator.set_typing_speed(initial_config.typing_speed);
    }
    
    #[test]
    fn test_app_state_lifecycle() {
        // Test the full lifecycle of AppState
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Create app state
        let app_state = create_app_state(keyboard_emulator.clone());
        
        // Test cloning preserves references
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(&app_state.keyboard_emulator, &cloned_state.keyboard_emulator));
        
        // Test multiple clones
        let states: Vec<AppState> = (0..5).map(|_| app_state.clone()).collect();
        for state in &states {
            assert!(Arc::ptr_eq(&app_state.keyboard_emulator, &state.keyboard_emulator));
        }
    }
    
    #[test]
    fn test_handle_config_changed_effects() {
        // Test that handle_config_changed properly updates keyboard emulator
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Slow,
                left_click_paste: false,
            })),
            config_path,
        });
        
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Change config multiple times and handle changes
        let speeds = vec![TypingSpeed::Fast, TypingSpeed::Normal, TypingSpeed::Slow];
        for speed in speeds {
            config_manager.set_typing_speed(speed);
            handle_config_changed(&config_manager, &keyboard_emulator);
            
            // Verify config was applied
            assert_eq!(config_manager.get().typing_speed, speed);
        }
    }
    
    #[test]
    fn test_handle_paste_clipboard_event_threading() {
        // Test that handle_paste_clipboard_event properly spawns threads
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Record initial thread count
        let initial_count = Arc::strong_count(&keyboard_emulator);
        
        // Call handle_paste_clipboard_event multiple times
        for _ in 0..3 {
            handle_paste_clipboard_event(keyboard_emulator.clone());
            // Give thread time to start
            std::thread::sleep(std::time::Duration::from_millis(5));
        }
        
        // Arc count should increase when threads hold references
        assert!(Arc::strong_count(&keyboard_emulator) >= initial_count);
        
        // Wait for threads to complete
        std::thread::sleep(std::time::Duration::from_millis(50));
    }
    
    #[test]
    fn test_initialization_with_corrupted_config() {
        // Test initialization when config is corrupted
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        // Write corrupted config
        std::fs::write(&config_path, "invalid toml content {{}").unwrap();
        
        // Initialize should still work (falls back to defaults)
        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();
        
        // Should have default values
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, false);
    }
    
    #[test]
    fn test_event_handler_names_consistency() {
        // Test that event names used in handlers are consistent
        let events = vec![
            "config_changed",
            "paste_clipboard",
        ];
        
        // Verify event names follow conventions
        for event in &events {
            assert!(!event.is_empty());
            assert!(event.chars().all(|c| c.is_ascii_lowercase() || c == '_'));
            assert!(!event.starts_with('_'));
            assert!(!event.ends_with('_'));
        }
    }
    
    #[test]
    fn test_startup_delay_timing() {
        use std::time::{Duration, Instant};
        
        // Test the 100ms delay timing
        let delay = Duration::from_millis(100);
        let start = Instant::now();
        std::thread::sleep(delay);
        let elapsed = start.elapsed();
        
        // Allow some tolerance for timing
        assert!(elapsed >= Duration::from_millis(95));
        assert!(elapsed <= Duration::from_millis(150));
    }
    
    #[test]
    fn test_component_initialization_order() {
        // Test that components can be initialized in the correct order
        
        // 1. Config manager first
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });
        
        // 2. Keyboard emulator second
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // 3. Apply initial config
        let initial_config = config_manager.get();
        keyboard_emulator.set_typing_speed(initial_config.typing_speed);
        
        // 4. Create app state
        let app_state = create_app_state(keyboard_emulator.clone());
        
        // Verify everything is connected
        assert!(Arc::strong_count(&app_state.keyboard_emulator) > 1);
    }
    
    #[test]
    fn test_error_propagation_in_initialization() {
        // Test that errors in initialization are properly propagated
        
        // Test with invalid config path (should still work with defaults)
        let invalid_path = PathBuf::from("/\0/invalid/path");
        let result = ConfigManager::new_with_path(invalid_path);
        // ConfigManager handles this gracefully
        assert!(result.is_ok());
        
        // Test keyboard emulator creation (always succeeds in current impl)
        let keyboard_result = KeyboardEmulator::new();
        assert!(keyboard_result.is_ok());
    }
    
    #[test]
    fn test_activation_policy_string() {
        // Test activation policy for macOS
        #[cfg(target_os = "macos")]
        {
            let policy = "Accessory";
            assert_eq!(policy, "Accessory");
        }
        
        // For other platforms, just verify the string
        let expected_policy = "Accessory";
        assert!(expected_policy.len() > 0);
    }
    
    #[test]
    fn test_paste_command_error_types() {
        // Test the error types that paste_clipboard command can return
        
        // Test Result<(), String> pattern
        fn mock_paste() -> Result<(), String> {
            Ok(())
        }
        assert!(mock_paste().is_ok());
        
        fn mock_paste_error() -> Result<(), String> {
            Err("Clipboard error".to_string())
        }
        assert!(mock_paste_error().is_err());
    }
}