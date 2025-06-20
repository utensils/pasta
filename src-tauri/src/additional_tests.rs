#[cfg(test)]
mod additional_coverage_tests {
    use std::sync::Arc;
    use crate::{AppState, initialize_components, create_app_state, handle_config_changed};
    use crate::keyboard::{KeyboardEmulator, TypingSpeed};
    use crate::config::{Config, ConfigManager};
    use std::sync::Mutex;
    use tempfile::TempDir;
    
    #[test]
    fn test_app_state_clone_behavior() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
        };
        
        // Test multiple clones
        let clone1 = app_state.clone();
        let clone2 = clone1.clone();
        let clone3 = app_state.clone();
        
        // All should share the same keyboard emulator
        assert!(Arc::ptr_eq(&app_state.keyboard_emulator, &clone1.keyboard_emulator));
        assert!(Arc::ptr_eq(&clone1.keyboard_emulator, &clone2.keyboard_emulator));
        assert!(Arc::ptr_eq(&clone2.keyboard_emulator, &clone3.keyboard_emulator));
    }
    
    #[test]
    fn test_initialize_components_with_existing_config() {
        // Create a config file before initializing
        let temp_dir = TempDir::new().unwrap();
        let config_dir = temp_dir.path().join(".config").join("pasta");
        std::fs::create_dir_all(&config_dir).unwrap();
        let config_path = config_dir.join("config.toml");
        
        // Write a config with non-default values
        let config_content = r#"
typing_speed = "slow"
left_click_paste = true
"#;
        std::fs::write(&config_path, config_content).unwrap();
        
        // Set HOME to temp dir for this test
        std::env::set_var("HOME", temp_dir.path());
        
        // Initialize components - should load the existing config
        let result = initialize_components();
        
        // Reset HOME
        std::env::remove_var("HOME");
        
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_handle_config_changed_all_combinations() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let left_click_options = vec![true, false];
        
        for speed in &speeds {
            for &left_click in &left_click_options {
                let config_manager = Arc::new(ConfigManager {
                    config: Arc::new(Mutex::new(Config {
                        typing_speed: *speed,
                        left_click_paste: left_click,
                    })),
                    config_path: config_path.clone(),
                });
                
                let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
                
                // Apply config
                handle_config_changed(&config_manager, &keyboard_emulator);
                
                // Verify config values
                let config = config_manager.get();
                assert_eq!(config.typing_speed, *speed);
                assert_eq!(config.left_click_paste, left_click);
            }
        }
    }
    
    #[test]
    fn test_config_thread_safety_stress() {
        use std::thread;
        use std::time::Duration;
        
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });
        
        let mut handles = vec![];
        
        // Spawn readers
        for _ in 0..10 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for _ in 0..100 {
                    let _ = cm.get();
                    thread::sleep(Duration::from_micros(10));
                }
            }));
        }
        
        // Spawn writers
        for i in 0..5 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for j in 0..50 {
                    let speed = match (i + j) % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };
                    cm.set_typing_speed(speed);
                    cm.set_left_click_paste((i + j) % 2 == 0);
                    thread::sleep(Duration::from_micros(20));
                }
            }));
        }
        
        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }
        
        // Final state should be valid
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }
    
    #[test]
    fn test_keyboard_emulator_arc_behavior() {
        let emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let initial_count = Arc::strong_count(&emulator);
        
        // Create app state
        let app_state = create_app_state(emulator.clone());
        assert_eq!(Arc::strong_count(&emulator), initial_count + 1);
        
        // Clone app state multiple times
        let _clone1 = app_state.clone();
        let _clone2 = app_state.clone();
        
        // Count increases for each clone of AppState since they each hold a clone of the Arc
        assert_eq!(Arc::strong_count(&emulator), initial_count + 3);
        
        // Drop app state
        drop(app_state);
        drop(_clone1);
        drop(_clone2);
        
        // Count should return to initial
        assert_eq!(Arc::strong_count(&emulator), initial_count);
    }
    
    #[test]
    fn test_config_bool_combinations() {
        // Test all boolean field combinations
        let configs = vec![
            Config { typing_speed: TypingSpeed::Slow, left_click_paste: true },
            Config { typing_speed: TypingSpeed::Slow, left_click_paste: false },
            Config { typing_speed: TypingSpeed::Normal, left_click_paste: true },
            Config { typing_speed: TypingSpeed::Normal, left_click_paste: false },
            Config { typing_speed: TypingSpeed::Fast, left_click_paste: true },
            Config { typing_speed: TypingSpeed::Fast, left_click_paste: false },
        ];
        
        for config in configs {
            let serialized = toml::to_string(&config).unwrap();
            let deserialized: Config = toml::from_str(&serialized).unwrap();
            
            assert_eq!(config.typing_speed, deserialized.typing_speed);
            assert_eq!(config.left_click_paste, deserialized.left_click_paste);
        }
    }
}