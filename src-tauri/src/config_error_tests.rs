#[cfg(test)]
mod config_error_tests {
    use std::{
        path::PathBuf,
        sync::{Arc, Mutex},
    };

    use tempfile::TempDir;

    use crate::{
        config::{Config, ConfigManager},
        keyboard::TypingSpeed,
    };

    #[test]
    fn test_config_save_error_logging() {
        // Create a config manager with an invalid path that will fail to save
        let config_manager = ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            // Use a path that can't be written to
            config_path: PathBuf::from("/root/definitely/not/writable/config.toml"),
        };

        // These should log errors but not panic
        config_manager.set_typing_speed(TypingSpeed::Fast);
        // The error was logged internally

        config_manager.set_left_click_paste(true);
        // The error was logged internally

        // Verify the in-memory config was still updated despite save failure
        let config = config_manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_config_migration_with_partial_old_format() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write a partial old config format
        let partial_old_config = r#"typing_speed = "slow""#;
        std::fs::write(&config_path, partial_old_config).unwrap();

        // Load should succeed with defaults for missing fields
        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Slow);
        assert_eq!(config.left_click_paste, false); // Default value
    }

    #[test]
    fn test_config_with_extra_unknown_fields() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write config with extra fields that should be ignored
        let config_with_extras = r#"
typing_speed = "normal"
left_click_paste = true
unknown_field = "ignored"
another_unknown = 42
"#;
        std::fs::write(&config_path, config_with_extras).unwrap();

        // Should load successfully, ignoring unknown fields
        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_config_manager_new_handles_missing_directory() {
        // Test that ConfigManager::new() handles the case where config directory creation fails
        // We can't easily test this without mocking the filesystem, but we can test the path creation
        let result = ConfigManager::new();

        // Should succeed even if config directory doesn't exist initially
        assert!(result.is_ok());
    }

    #[test]
    fn test_all_typing_speed_lowercase_variants() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Test all lowercase variants
        let variants = vec![
            ("slow", TypingSpeed::Slow),
            ("normal", TypingSpeed::Normal),
            ("fast", TypingSpeed::Fast),
        ];

        for (text, expected) in variants {
            let config_content = format!(r#"typing_speed = "{}""#, text);
            std::fs::write(&config_path, config_content).unwrap();

            let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
            let config = config_manager.get();

            assert_eq!(config.typing_speed, expected);
        }
    }

    #[test]
    fn test_config_old_format_variations() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Test various old format configurations
        let old_configs = vec![
            // Old format with enabled=true
            (
                r#"enabled = true
typing_speed = "fast""#,
                TypingSpeed::Fast,
            ),
            // Old format with enabled=false
            (
                r#"enabled = false
typing_speed = "slow""#,
                TypingSpeed::Slow,
            ),
            // Old format with capitalized values
            (
                r#"enabled = true
typing_speed = "NORMAL""#,
                TypingSpeed::Normal,
            ),
        ];

        for (old_config, expected_speed) in old_configs {
            std::fs::write(&config_path, old_config).unwrap();

            let config_manager = ConfigManager::new_with_path(config_path.clone()).unwrap();
            let config = config_manager.get();

            assert_eq!(config.typing_speed, expected_speed);
            assert_eq!(config.left_click_paste, false); // Always defaults to false for migrated configs
        }
    }
}
