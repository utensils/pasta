use crate::keyboard::TypingSpeed;
use dirs::config_dir;
use log::{debug, error};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub enabled: bool,
    pub typing_speed: TypingSpeed,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            enabled: true,
            typing_speed: TypingSpeed::Normal,
        }
    }
}

pub struct ConfigManager {
    config: Arc<Mutex<Config>>,
    config_path: PathBuf,
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
        let config_dir = config_dir()
            .ok_or("Failed to get config directory")?;
        
        let app_config_dir = config_dir.join("pasta-rust");
        fs::create_dir_all(&app_config_dir)?;
        
        Ok(app_config_dir.join("config.toml"))
    }

    fn load_config(path: &PathBuf) -> Result<Config, Box<dyn std::error::Error>> {
        if path.exists() {
            debug!("Loading config from {:?}", path);
            let content = fs::read_to_string(path)?;
            let config: Config = toml::from_str(&content)?;
            Ok(config)
        } else {
            debug!("Config file not found, using defaults");
            Ok(Config::default())
        }
    }

    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        let config = self.config.lock().unwrap();
        let content = toml::to_string(&*config)?;
        fs::write(&self.config_path, content)?;
        debug!("Config saved to {:?}", self.config_path);
        Ok(())
    }

    pub fn get(&self) -> Config {
        self.config.lock().unwrap().clone()
    }

    pub fn set_enabled(&self, enabled: bool) {
        self.config.lock().unwrap().enabled = enabled;
        if let Err(e) = self.save() {
            error!("Failed to save config: {:?}", e);
        }
    }

    pub fn set_typing_speed(&self, speed: TypingSpeed) {
        self.config.lock().unwrap().typing_speed = speed;
        if let Err(e) = self.save() {
            error!("Failed to save config: {:?}", e);
        }
    }
}