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
}

impl Default for Config {
    fn default() -> Self {
        Self {
            typing_speed: TypingSpeed::Normal,
        }
    }
}

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

            // Try to parse the new format first
            match toml::from_str::<Config>(&content) {
                Ok(config) => Ok(config),
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
                            Ok(Config { typing_speed })
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
        };

        let serialized = toml::to_string(&config).unwrap();
        assert!(serialized.contains("typing_speed"));
        assert!(serialized.contains("slow"));
        assert!(!serialized.contains("enabled"));
    }

    #[test]
    fn test_config_deserialization() {
        let toml_str = r#"typing_speed = "fast""#;
        let config: Config = toml::from_str(toml_str).unwrap();
        assert_eq!(config.typing_speed, TypingSpeed::Fast);
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
            assert!(matches!(speed, TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast));
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
        };
        let cloned = config.clone();
        assert_eq!(config.typing_speed, cloned.typing_speed);
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
            let config = Config { typing_speed: speed };
            let serialized = toml::to_string(&config).unwrap();
            let deserialized: Config = toml::from_str(&serialized).unwrap();
            assert_eq!(config.typing_speed, deserialized.typing_speed);
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
}