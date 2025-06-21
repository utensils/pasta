#[cfg(test)]
mod config_debug_tests {
    use std::sync::{Arc, Mutex};

    use tempfile::TempDir;

    use crate::{
        config::{Config, ConfigManager},
        keyboard::TypingSpeed,
    };

    #[test]
    fn test_config_load_with_debug_logging() {
        // Initialize logger for testing to ensure debug! macros are executed
        let _ = env_logger::builder()
            .filter_level(log::LevelFilter::Debug)
            .try_init();

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write a valid config to trigger debug logging
        let config_content = r#"
typing_speed = "fast"
left_click_paste = true
"#;
        std::fs::write(&config_path, config_content).unwrap();

        // Load config - this should trigger debug logging
        let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_config_migration_with_debug_logging() {
        let _ = env_logger::builder()
            .filter_level(log::LevelFilter::Debug)
            .try_init();

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write old format to trigger migration debug logging
        let old_config = r#"
enabled = true
typing_speed = "normal"
"#;
        std::fs::write(&config_path, old_config).unwrap();

        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_config_save_failure_with_logging() {
        let _ = env_logger::builder()
            .filter_level(log::LevelFilter::Error)
            .try_init();

        // Create a config manager with a path that will fail
        let config_manager = ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path: std::path::PathBuf::from("/definitely/not/writable/path/config.toml"),
        };

        // These should trigger error logging
        config_manager.set_typing_speed(TypingSpeed::Slow);
        config_manager.set_left_click_paste(true);

        // Verify the config was updated in memory despite save failure
        let config = config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Slow);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_all_config_edge_cases() {
        // Test 1: Empty TOML file
        {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");
            std::fs::write(&config_path, "").unwrap();
            let config_manager = ConfigManager::new_with_path(config_path).unwrap();
            assert_eq!(config_manager.get().typing_speed, TypingSpeed::Normal);
        }

        // Test 2: Partial config (only typing_speed)
        {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");
            std::fs::write(&config_path, "typing_speed = \"slow\"").unwrap();
            let config_manager = ConfigManager::new_with_path(config_path).unwrap();
            assert_eq!(config_manager.get().typing_speed, TypingSpeed::Slow);
            assert_eq!(config_manager.get().left_click_paste, false);
        }

        // Test 3: Partial config (only left_click_paste) - This will use defaults since typing_speed is required
        {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");
            std::fs::write(&config_path, "left_click_paste = true").unwrap();
            let config_manager = ConfigManager::new_with_path(config_path).unwrap();
            // Since typing_speed is required but missing, it should fall back to defaults
            assert_eq!(config_manager.get().typing_speed, TypingSpeed::Normal);
            assert_eq!(config_manager.get().left_click_paste, false); // Default value
        }

        // Test 4: Config with comments
        {
            let temp_dir = TempDir::new().unwrap();
            let config_path = temp_dir.path().join("config.toml");
            let config_with_comments = r#"
# This is a comment
typing_speed = "fast" # Another comment
left_click_paste = false
"#;
            std::fs::write(&config_path, config_with_comments).unwrap();
            let config_manager = ConfigManager::new_with_path(config_path).unwrap();
            assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
            assert_eq!(config_manager.get().left_click_paste, false);
        }
    }

    #[test]
    fn test_config_unicode_handling() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Test config with unicode in comments
        let config_with_unicode = r#"
# Config файл 配置文件 🦀
typing_speed = "normal"
left_click_paste = true
"#;
        std::fs::write(&config_path, config_with_unicode).unwrap();

        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, true);
    }
}
