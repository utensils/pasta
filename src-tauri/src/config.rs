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

        let app_config_dir = config_dir.join("pasta-rust");
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
                            let typing_speed = match old_config.typing_speed.to_lowercase().as_str() {
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
}