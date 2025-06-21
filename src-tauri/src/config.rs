use std::{
    fs,
    path::PathBuf,
    sync::{Arc, Mutex},
};

use dirs::config_dir;
use log::{debug, error};
use serde::{Deserialize, Serialize};

use crate::keyboard::TypingSpeed;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub typing_speed: TypingSpeed,
    #[serde(default)]
    pub left_click_paste: bool,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            typing_speed: TypingSpeed::Normal,
            left_click_paste: false, // Default to false (both buttons show menu)
        }
    }
}

#[derive(Debug)]
pub struct ConfigManager {
    pub(crate) config: Arc<Mutex<Config>>,
    pub(crate) config_path: PathBuf,
}

impl ConfigManager {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let config_path = Self::get_config_path()?;
        let config = Self::load_config(&config_path)?;

        Ok(Self {
            config: Arc::new(Mutex::new(config)),
            config_path,
        })
    }

    pub fn new_with_path(config_path: PathBuf) -> Result<Self, Box<dyn std::error::Error>> {
        let config = Self::load_config(&config_path)?;

        Ok(Self {
            config: Arc::new(Mutex::new(config)),
            config_path,
        })
    }

    fn get_config_path() -> Result<PathBuf, Box<dyn std::error::Error>> {
        let config_dir = config_dir().ok_or("Failed to get config directory")?;

        let app_config_dir = config_dir.join("pasta");
        fs::create_dir_all(&app_config_dir)?;

        Ok(app_config_dir.join("config.toml"))
    }

    fn load_config(path: &PathBuf) -> Result<Config, Box<dyn std::error::Error>> {
        if path.exists() {
            debug!("Loading config from {path:?}");
            let content = fs::read_to_string(path)?;
            debug!("Config file contents: {content}");

            // Try to parse the new format first
            match toml::from_str::<Config>(&content) {
                Ok(config) => {
                    debug!(
                        "Loaded config: typing_speed={:?}, left_click_paste={}",
                        config.typing_speed, config.left_click_paste
                    );
                    Ok(config)
                }
                Err(_) => {
                    // If that fails, try to parse the old format and migrate
                    #[derive(Deserialize)]
                    struct OldConfig {
                        #[allow(dead_code)]
                        enabled: bool,
                        typing_speed: String,
                    }

                    match toml::from_str::<OldConfig>(&content) {
                        Ok(old_config) => {
                            debug!("Migrating old config format");
                            // Convert old capitalized values to lowercase
                            let typing_speed = match old_config.typing_speed.to_lowercase().as_str()
                            {
                                "slow" => TypingSpeed::Slow,
                                "normal" => TypingSpeed::Normal,
                                "fast" => TypingSpeed::Fast,
                                _ => TypingSpeed::Normal, // Default fallback
                            };
                            Ok(Config {
                                typing_speed,
                                left_click_paste: false, // Default for migrated configs
                            })
                        }
                        Err(_) => {
                            // If both formats fail, just use defaults
                            debug!("Failed to parse config, using defaults");
                            Ok(Config::default())
                        }
                    }
                }
            }
        } else {
            debug!("Config file not found, using defaults");
            Ok(Config::default())
        }
    }

    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let config = self.config.lock().unwrap();
        let content = toml::to_string(&*config)?;
        fs::write(&self.config_path, content)?;
        debug!("Config saved to {}", self.config_path.display());
        Ok(())
    }

    pub fn get(&self) -> Config {
        self.config.lock().unwrap().clone()
    }

    pub fn set_typing_speed(&self, speed: TypingSpeed) {
        self.config.lock().unwrap().typing_speed = speed;
        if let Err(e) = self.save() {
            error!("Failed to save config: {e:?}");
        }
    }

    pub fn set_left_click_paste(&self, enabled: bool) {
        self.config.lock().unwrap().left_click_paste = enabled;
        if let Err(e) = self.save() {
            error!("Failed to save config: {e:?}");
        }
    }
}

#[cfg(test)]
mod tests {
    use tempfile::TempDir;

    use super::*;

    struct TestConfigManager {
        manager: ConfigManager,
        _temp_dir: TempDir,
    }

    impl TestConfigManager {
        fn new() -> Result<Self, Box<dyn std::error::Error>> {
            let temp_dir = TempDir::new()?;
            let config_path = temp_dir.path().join("config.toml");

            let manager = ConfigManager {
                config: Arc::new(Mutex::new(Config::default())),
                config_path,
            };

            Ok(Self {
                manager,
                _temp_dir: temp_dir,
            })
        }
    }

    #[test]
    fn test_config_default() {
        let config = Config::default();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, false);
    }

    #[test]
    fn test_config_manager_save_and_load() {
        let test_manager = TestConfigManager::new().unwrap();
        let manager = test_manager.manager;

        // Change config
        manager.set_typing_speed(TypingSpeed::Fast);

        // Save should work
        manager.save().unwrap();

        // Load config from file
        let loaded_config = ConfigManager::load_config(&manager.config_path).unwrap();
        assert_eq!(loaded_config.typing_speed, TypingSpeed::Fast);
    }

    #[test]
    fn test_config_manager_get() {
        let test_manager = TestConfigManager::new().unwrap();
        let manager = test_manager.manager;

        let config = manager.get();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_config_manager_set_typing_speed() {
        let test_manager = TestConfigManager::new().unwrap();
        let manager = test_manager.manager;

        manager.set_typing_speed(TypingSpeed::Slow);
        assert_eq!(manager.get().typing_speed, TypingSpeed::Slow);

        manager.set_typing_speed(TypingSpeed::Fast);
        assert_eq!(manager.get().typing_speed, TypingSpeed::Fast);
    }

    #[test]
    fn test_config_manager_set_left_click_paste() {
        let test_manager = TestConfigManager::new().unwrap();
        let manager = test_manager.manager;

        // Test default is false
        assert_eq!(manager.get().left_click_paste, false);

        // Test setting to true
        manager.set_left_click_paste(true);
        assert_eq!(manager.get().left_click_paste, true);

        // Test setting back to false
        manager.set_left_click_paste(false);
        assert_eq!(manager.get().left_click_paste, false);
    }

    #[test]
    fn test_config_migration() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write old format config with lowercase
        let old_config = r#"
enabled = true
typing_speed = "fast"
"#;
        fs::write(&config_path, old_config).unwrap();

        // Load should migrate successfully
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
    }

    #[test]
    fn test_config_migration_capitalized() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write old format config with capitalized values
        let old_config = r#"
enabled = true
typing_speed = "Normal"
"#;
        fs::write(&config_path, old_config).unwrap();

        // Load should migrate successfully
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_config_serialization() {
        let config = Config {
            typing_speed: TypingSpeed::Slow,
            left_click_paste: true,
        };

        let serialized = toml::to_string(&config).unwrap();
        assert!(serialized.contains("typing_speed"));
        assert!(serialized.contains("slow"));
        assert!(serialized.contains("left_click_paste"));
        assert!(serialized.contains("true"));
        assert!(!serialized.contains("enabled"));
    }

    #[test]
    fn test_config_deserialization() {
        let toml_str = r#"typing_speed = "fast""#;
        let config: Config = toml::from_str(toml_str).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, false); // Should use default
    }

    #[test]
    fn test_config_deserialization_with_left_click_paste() {
        let toml_str = r#"
typing_speed = "normal"
left_click_paste = true
"#;
        let config: Config = toml::from_str(toml_str).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, true);
    }

    #[test]
    fn test_invalid_config_fallback() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write invalid config
        let invalid_config = r#"invalid = true"#;
        fs::write(&config_path, invalid_config).unwrap();

        // Should fall back to defaults
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_corrupted_config_handling() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write corrupted config
        fs::write(&config_path, "not valid toml at all {{{").unwrap();

        // Should fall back to defaults without panicking
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_empty_config_file() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write empty file
        fs::write(&config_path, "").unwrap();

        // Should fall back to defaults
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_config_path_creation() {
        // Just test that get_config_path doesn't panic
        let result = ConfigManager::get_config_path();
        assert!(result.is_ok());
        let path = result.unwrap();
        assert!(path.ends_with("config.toml"));
        assert!(path.to_string_lossy().contains("pasta"));
    }

    #[test]
    fn test_config_thread_safety() {
        use std::thread;

        let test_manager = TestConfigManager::new().unwrap();
        let manager = Arc::new(test_manager.manager);

        let handles: Vec<_> = (0..3)
            .map(|i| {
                let m = manager.clone();
                thread::spawn(move || {
                    let speed = match i % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };
                    m.set_typing_speed(speed);
                    m.get().typing_speed
                })
            })
            .collect();

        for handle in handles {
            let speed = handle.join().unwrap();
            assert!(matches!(
                speed,
                TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
            ));
        }
    }

    #[test]
    fn test_migration_with_unknown_speed() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write old format config with unknown speed
        let old_config = r#"
enabled = false
typing_speed = "SuperFast"
"#;
        fs::write(&config_path, old_config).unwrap();

        // Should default to Normal
        let config = ConfigManager::load_config(&config_path).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_config_clone() {
        let config = Config {
            typing_speed: TypingSpeed::Fast,
            left_click_paste: true,
        };
        let cloned = config.clone();
        assert_eq!(config.typing_speed, cloned.typing_speed);
        assert_eq!(config.left_click_paste, cloned.left_click_paste);
    }

    #[test]
    fn test_config_debug() {
        let config = Config::default();
        let debug_str = format!("{:?}", config);
        assert!(debug_str.contains("Config"));
        assert!(debug_str.contains("typing_speed"));
    }

    #[test]
    fn test_all_typing_speeds() {
        // Test all variants of TypingSpeed
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

        for speed in speeds {
            let config = Config {
                typing_speed: speed,
                left_click_paste: false,
            };
            let serialized = toml::to_string(&config).unwrap();
            let deserialized: Config = toml::from_str(&serialized).unwrap();
            assert_eq!(config.typing_speed, deserialized.typing_speed);
            assert_eq!(config.left_click_paste, deserialized.left_click_paste);
        }
    }

    #[test]
    fn test_save_error_handling() {
        // Create a config manager with an invalid path
        let manager = ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path: PathBuf::from("/invalid/path/that/does/not/exist/config.toml"),
        };

        // Save should fail but not panic
        let result = manager.save();
        assert!(result.is_err());
    }

    #[test]
    fn test_config_manager_debug() {
        // Test Debug trait implementation
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path: config_path.clone(),
        };

        let debug_str = format!("{:?}", config_manager);
        assert!(debug_str.contains("ConfigManager"));
    }

    #[test]
    fn test_config_partial_parse() {
        // Test that partial configs work
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        // Write partial config (missing fields)
        let partial_toml = r#"typing_speed = "fast""#;
        std::fs::write(&config_path, partial_toml).unwrap();

        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        assert_eq!(config.typing_speed, TypingSpeed::Fast);
        assert_eq!(config.left_click_paste, false); // Default value
    }

    #[test]
    fn test_config_edge_case_values() {
        // Test edge case typing speed values
        let config1 = Config {
            typing_speed: TypingSpeed::Slow,
            left_click_paste: true,
        };

        let config2 = Config {
            typing_speed: TypingSpeed::Fast,
            left_click_paste: false,
        };

        // Test inequality
        assert_ne!(config1.typing_speed, config2.typing_speed);
        assert_ne!(config1.left_click_paste, config2.left_click_paste);
    }

    #[test]
    fn test_typing_speed_all_combinations() {
        // Test all possible typing speed values
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

        for speed in &speeds {
            let config = Config {
                typing_speed: *speed,
                left_click_paste: false,
            };

            let serialized = toml::to_string(&config).unwrap();
            let deserialized: Config = toml::from_str(&serialized).unwrap();

            assert_eq!(config.typing_speed, deserialized.typing_speed);
        }
    }

    #[test]
    fn test_config_concurrent_read_write() {
        use std::thread;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager::new_with_path(config_path).unwrap());

        // Spawn reader threads
        let mut handles = vec![];
        for _ in 0..3 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for _ in 0..10 {
                    let _config = cm.get();
                }
            }));
        }

        // Spawn writer threads
        for i in 0..2 {
            let cm = config_manager.clone();
            handles.push(thread::spawn(move || {
                for j in 0..5 {
                    let speed = match (i + j) % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };
                    cm.set_typing_speed(speed);
                }
            }));
        }

        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }

        // Verify final state is valid
        let final_config = config_manager.get();
        assert!(matches!(
            final_config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));
    }

    #[test]
    fn test_config_path_platform_specific() {
        // Test that get_config_path returns appropriate paths
        let result = ConfigManager::get_config_path();
        assert!(result.is_ok());

        let path = result.unwrap();
        assert!(path.to_string_lossy().contains("pasta"));
        assert!(path.to_string_lossy().contains("config.toml"));
    }

    #[test]
    fn test_config_path_with_deep_nesting() {
        let temp_dir = TempDir::new().unwrap();
        let nested_path = temp_dir
            .path()
            .join("deep")
            .join("nested")
            .join("config.toml");

        // Create parent directories
        std::fs::create_dir_all(nested_path.parent().unwrap()).unwrap();

        // Create config at nested path
        let config_manager = ConfigManager::new_with_path(nested_path.clone()).unwrap();
        config_manager.set_typing_speed(TypingSpeed::Slow);

        // Verify file was created
        assert!(nested_path.exists());

        // Load and verify
        let loaded_config = ConfigManager::load_config(&nested_path).unwrap();
        assert_eq!(loaded_config.typing_speed, TypingSpeed::Slow);
    }

    #[test]
    fn test_old_config_format_with_unknown_fields() {
        // Test that old config with extra fields still works
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let old_config_with_extra = r#"
            enabled = true
            typing_speed = "normal"
            extra_field = "ignored"
            another_field = 42
        "#;

        std::fs::write(&config_path, old_config_with_extra).unwrap();

        let config_manager = ConfigManager::new_with_path(config_path).unwrap();
        let config = config_manager.get();

        // Should still load with defaults
        assert_eq!(config.typing_speed, TypingSpeed::Normal);
        assert_eq!(config.left_click_paste, false);
    }
}
