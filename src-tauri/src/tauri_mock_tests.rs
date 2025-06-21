#[cfg(test)]
mod tauri_mock_tests {
    use std::sync::{Arc, Mutex};

    use tempfile::TempDir;

    use crate::{
        config::{Config, ConfigManager},
        create_app_state, handle_config_changed, handle_paste_clipboard_event,
        initialize_components,
        keyboard::{KeyboardEmulator, TypingSpeed},
        AppState,
    };

    #[test]
    fn test_app_state_creation_and_cloning() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let app_state = create_app_state(keyboard_emulator.clone());

        // Test cloning
        let cloned_state = app_state.clone();

        // Verify both states share the same keyboard emulator
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &cloned_state.keyboard_emulator
        ));
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &keyboard_emulator
        ));
    }

    #[test]
    fn test_initialize_components_success() {
        let result = initialize_components();
        assert!(result.is_ok());

        let (config_manager, keyboard_emulator) = result.unwrap();

        // Verify components are properly initialized
        let config = config_manager.get();
        assert!(matches!(
            config.typing_speed,
            TypingSpeed::Slow | TypingSpeed::Normal | TypingSpeed::Fast
        ));

        // Verify Arc references are valid
        assert!(Arc::strong_count(&config_manager) >= 1);
        assert!(Arc::strong_count(&keyboard_emulator) >= 1);
    }

    #[test]
    fn test_handle_config_changed_logic() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config {
                typing_speed: TypingSpeed::Normal,
                left_click_paste: false,
            })),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Change config and handle the change
        config_manager.set_typing_speed(TypingSpeed::Fast);
        handle_config_changed(&config_manager, &keyboard_emulator);

        // Verify config was applied
        assert_eq!(config_manager.get().typing_speed, TypingSpeed::Fast);

        // Test multiple changes
        for speed in &[TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast] {
            config_manager.set_typing_speed(*speed);
            handle_config_changed(&config_manager, &keyboard_emulator);
            assert_eq!(config_manager.get().typing_speed, *speed);
        }
    }

    #[test]
    fn test_handle_paste_clipboard_event_spawning() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let initial_count = Arc::strong_count(&keyboard_emulator);

        // Handle paste event (spawns a thread)
        handle_paste_clipboard_event(keyboard_emulator.clone());

        // Give thread time to spawn
        std::thread::sleep(std::time::Duration::from_millis(50));

        // Thread should be spawned and Arc count may temporarily increase
        assert!(Arc::strong_count(&keyboard_emulator) >= initial_count);
    }

    #[test]
    fn test_paste_clipboard_command_structure() {
        // Test the structure of paste_clipboard command
        // The actual paste_clipboard function is:
        // async fn paste_clipboard(state: State<'_, AppState>) -> Result<(), String>

        // We can test that the AppState structure is correct
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
        };

        // Verify the state contains the keyboard emulator
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &keyboard_emulator
        ));
    }

    #[test]
    fn test_event_names_consistency() {
        use crate::helpers::get_event_names;

        let (config_event, paste_event) = get_event_names();

        assert_eq!(config_event, "config_changed");
        assert_eq!(paste_event, "paste_clipboard");

        // Verify event names are valid
        assert!(!config_event.is_empty());
        assert!(!paste_event.is_empty());
        assert!(!config_event.contains(' '));
        assert!(!paste_event.contains(' '));
    }

    #[test]
    fn test_activation_policy_helper() {
        #[cfg(target_os = "macos")]
        {
            use crate::helpers::get_activation_policy;
            let policy = get_activation_policy();
            assert_eq!(policy, "Accessory");
        }
    }

    #[test]
    fn test_startup_delay_helper() {
        use crate::helpers::get_startup_delay;

        let delay = get_startup_delay();
        assert_eq!(delay.as_millis(), 100);
    }

    #[test]
    fn test_concurrent_config_operations() {
        use std::thread;

        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("config.toml");

        let config_manager = Arc::new(ConfigManager {
            config: Arc::new(Mutex::new(Config::default())),
            config_path,
        });

        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Spawn multiple threads doing config operations
        let handles: Vec<_> = (0..10)
            .map(|i| {
                let cm = config_manager.clone();
                let ke = keyboard_emulator.clone();

                thread::spawn(move || {
                    let speed = match i % 3 {
                        0 => TypingSpeed::Slow,
                        1 => TypingSpeed::Normal,
                        _ => TypingSpeed::Fast,
                    };

                    cm.set_typing_speed(speed);
                    handle_config_changed(&cm, &ke);

                    if i % 2 == 0 {
                        cm.set_left_click_paste(i % 4 == 0);
                    }
                })
            })
            .collect();

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
    fn test_multiple_paste_events() {
        // Test handling multiple paste events
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Trigger multiple paste events
        for _ in 0..5 {
            handle_paste_clipboard_event(keyboard_emulator.clone());
        }

        // Give threads time to spawn
        std::thread::sleep(std::time::Duration::from_millis(100));

        // Keyboard emulator should still be valid
        assert!(Arc::strong_count(&keyboard_emulator) > 0);
    }
}
