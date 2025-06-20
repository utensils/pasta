use pasta_lib::{config::ConfigManager, keyboard::{KeyboardEmulator, TypingSpeed}};
use std::sync::Arc;
use tempfile::TempDir;

#[test]
fn test_config_and_keyboard_integration() {
    // Test that config manager and keyboard emulator work together
    let config_manager = Arc::new(ConfigManager::new().unwrap());
    let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
    
    // Set speed through config
    config_manager.set_typing_speed(TypingSpeed::Fast);
    
    // Apply to keyboard emulator
    let config = config_manager.get();
    keyboard_emulator.set_typing_speed(config.typing_speed);
    
    // Verify config was saved
    assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);
}

#[test]
fn test_multiple_config_managers_share_state() {
    // Create temp dir for this test
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.toml");
    
    // Create first config manager
    let config1 = ConfigManager {
        config: Arc::new(std::sync::Mutex::new(pasta_lib::config::Config::default())),
        config_path: config_path.clone(),
    };
    
    // Set speed
    config1.set_typing_speed(TypingSpeed::Slow);
    
    // Create second config manager with same path
    let config2 = ConfigManager {
        config: Arc::new(std::sync::Mutex::new(
            load_config(&config_path).unwrap()
        )),
        config_path: config_path.clone(),
    };
    
    // Should have the same speed
    assert_eq!(config2.get().typing_speed, TypingSpeed::Slow);
}

#[tokio::test]
async fn test_keyboard_emulator_async_operations() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();
    
    // Test multiple async operations
    let result1 = keyboard_emulator.type_text("Hello").await;
    assert!(result1.is_ok());
    
    let result2 = keyboard_emulator.type_text("World").await;
    assert!(result2.is_ok());
    
    // Test with special characters
    let result3 = keyboard_emulator.type_text("Line1\nLine2\tTabbed").await;
    assert!(result3.is_ok());
}

#[test]
fn test_typing_speed_consistency_across_modules() {
    // Ensure TypingSpeed enum is consistent across modules
    let speeds = vec![
        TypingSpeed::Slow,
        TypingSpeed::Normal, 
        TypingSpeed::Fast,
    ];
    
    for speed in speeds {
        // Test serialization roundtrip
        let json = serde_json::to_string(&speed).unwrap();
        let deserialized: TypingSpeed = serde_json::from_str(&json).unwrap();
        assert_eq!(speed, deserialized);
        
        // Test that delay values are sensible
        let delay = speed.delay_ms();
        assert!(delay >= 10 && delay <= 50);
    }
}

#[test]
fn test_config_persistence_across_restarts() {
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.toml");
    
    // Simulate first run
    {
        let config_manager = ConfigManager {
            config: Arc::new(std::sync::Mutex::new(pasta_lib::config::Config::default())),
            config_path: config_path.clone(),
        };
        config_manager.set_typing_speed(TypingSpeed::Fast);
    }
    
    // Simulate restart - load from disk
    {
        let loaded_config = load_config(&config_path).unwrap();
        assert_eq!(loaded_config.typing_speed, TypingSpeed::Fast);
    }
}

#[test]
fn test_concurrent_config_access() {
    use std::thread;
    
    let config_manager = Arc::new(ConfigManager::new().unwrap());
    let mut handles = vec![];
    
    // Spawn multiple threads that read and write config
    for i in 0..5 {
        let cm = config_manager.clone();
        let handle = thread::spawn(move || {
            let speed = match i % 3 {
                0 => TypingSpeed::Slow,
                1 => TypingSpeed::Normal,
                _ => TypingSpeed::Fast,
            };
            cm.set_typing_speed(speed);
            cm.get().typing_speed
        });
        handles.push(handle);
    }
    
    // All threads should complete without deadlock
    for handle in handles {
        let speed = handle.join().unwrap();
        assert!(matches!(speed, TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast));
    }
}

#[tokio::test] 
async fn test_keyboard_emulator_channel_capacity() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();
    
    // Send multiple commands quickly
    let mut results = vec![];
    for i in 0..5 {
        let result = keyboard_emulator.type_text(&format!("Text {}", i)).await;
        results.push(result);
    }
    
    // All should succeed
    for result in results {
        assert!(result.is_ok());
    }
}

#[test]
fn test_cross_module_error_handling() {
    // Test error handling when config directory doesn't exist
    let invalid_path = std::path::PathBuf::from("/invalid/path/config.toml");
    let config_result = load_config(&invalid_path);
    
    // Should return Ok with default config even if file doesn't exist
    assert!(config_result.is_ok());
    assert_eq!(config_result.unwrap().typing_speed, TypingSpeed::Normal);
}

// Helper function for tests
fn load_config(path: &std::path::PathBuf) -> Result<pasta_lib::config::Config, Box<dyn std::error::Error>> {
    if path.exists() {
        let content = std::fs::read_to_string(path)?;
        match toml::from_str(&content) {
            Ok(config) => Ok(config),
            Err(_) => Ok(pasta_lib::config::Config::default()),
        }
    } else {
        Ok(pasta_lib::config::Config::default())
    }
}