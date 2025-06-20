#[cfg(test)]
mod error_scenario_tests {
    use std::sync::Arc;
    use crate::{
        config::{Config, ConfigManager},
        keyboard::{KeyboardEmulator, TypingSpeed},
        app_logic::{handle_paste_clipboard, ClipboardProvider},
    };
    use tempfile::TempDir;

    // Test clipboard provider that always fails
    struct FailingClipboard;
    
    impl ClipboardProvider for FailingClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            Err("Simulated clipboard failure".to_string())
        }
    }

    // Test clipboard provider that returns None
    struct EmptyClipboard;
    
    impl ClipboardProvider for EmptyClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            Ok(None)
        }
    }

    #[tokio::test]
    async fn test_paste_clipboard_with_error() {
        let clipboard = FailingClipboard;
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Simulated clipboard failure");
    }

    #[tokio::test]
    async fn test_paste_clipboard_with_empty() {
        let clipboard = EmptyClipboard;
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_config_save_with_invalid_path() {
        let config_manager = ConfigManager {
            config: Arc::new(std::sync::Mutex::new(Config::default())),
            config_path: std::path::PathBuf::from("/root/nonexistent/path/config.toml"),
        };
        
        let result = config_manager.save();
        assert!(result.is_err());
    }

    #[test]
    fn test_config_load_corrupted_file() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        // Write invalid TOML
        std::fs::write(&config_path, "this is not valid [[[ toml").unwrap();
        
        // Should fall back to defaults
        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, false);
    }

    #[test]
    fn test_config_migration_edge_cases() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        // Test with mixed case typing speed
        let old_config = r#"
enabled = true
typing_speed = "FaSt"
"#;
        std::fs::write(&config_path, old_config).unwrap();
        
        let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
        let config = config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        
        // Test with invalid typing speed
        let old_config2 = r#"
enabled = false
typing_speed = "INVALID_SPEED"
"#;
        std::fs::write(&config_path, old_config2).unwrap();
        
        let config_manager2 = ConfigManager::new_with_path(config_path).unwrap();
        let config2 = config_manager2.get();
        assert_eq!(config2.typing_speed, TypingSpeed::Normal); // Should default
    }

    #[test]
    fn test_concurrent_config_writes() {
        use std::thread;
        
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");
        
        let config_manager = Arc::new(ConfigManager::new_with_path(config_path).unwrap());
        let mut handles = vec![];
        
        // Spawn multiple threads that write to config simultaneously
        for i in 0..10 {
            let cm = config_manager.clone();
            let handle = thread::spawn(move || {
                let speed = match i % 3 {
                    0 => TypingSpeed::Slow,
                    1 => TypingSpeed::Normal,
                    _ => TypingSpeed::Fast,
                };
                cm.set_typing_speed(speed);
                cm.set_left_click_paste(i % 2 == 0);
            });
            handles.push(handle);
        }
        
        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }
        
        // Config should still be valid
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }

    #[tokio::test]
    async fn test_keyboard_emulator_with_special_text() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        // Test with various special characters
        let special_texts = vec![
            "\n\n\n",  // Multiple newlines
            "\t\t\t",  // Multiple tabs
            "before\nmiddle\tafter",  // Mixed
            "",  // Empty string
            " ",  // Single space
            "🦀 Rust 🚀",  // Emoji
        ];
        
        for text in special_texts {
            let result = keyboard_emulator.type_text(text).await;
            assert!(result.is_ok());
        }
    }

    #[test]
    fn test_typing_speed_edge_values() {
        // Test all typing speeds have reasonable delays
        let speeds = vec![
            TypingSpeed::Slow,
            TypingSpeed::Normal,
            TypingSpeed::Fast,
        ];
        
        for speed in speeds {
            let delay = speed.delay_ms();
            assert!(delay >= 10, "Delay should be at least 10ms");
            assert!(delay <= 50, "Delay should be at most 50ms");
        }
    }
}