#[cfg(test)]
mod keyboard_mock_tests {
    use std::sync::{atomic::AtomicBool, Arc};

    use tokio::sync::mpsc;

    use crate::keyboard::{KeyboardCommand, TypingSpeed};

    #[test]
    fn test_keyboard_command_send_failures() {
        // Test keyboard command handling edge cases
        let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(1);

        // Fill the channel
        let _ = tx.try_send(KeyboardCommand::TypeText(
            "test".to_string(),
            Arc::new(AtomicBool::new(false)),
        ));

        // Try to send when full
        let result = tx.try_send(KeyboardCommand::SetSpeed(TypingSpeed::Fast));
        assert!(result.is_err());

        // Receive to clear
        let _ = rx.try_recv();

        // Now it should work
        let result = tx.try_send(KeyboardCommand::SetSpeed(TypingSpeed::Fast));
        assert!(result.is_ok());
    }

    #[test]
    fn test_typing_speed_serialization_all_formats() {
        // Test JSON serialization
        let speeds = vec![
            (TypingSpeed::Slow, "\"slow\""),
            (TypingSpeed::Normal, "\"normal\""),
            (TypingSpeed::Fast, "\"fast\""),
        ];

        for (speed, expected) in speeds {
            let json = serde_json::to_string(&speed).unwrap();
            assert_eq!(json, expected);

            // Test round-trip
            let deserialized: TypingSpeed = serde_json::from_str(&json).unwrap();
            assert_eq!(deserialized, speed);
        }

        // Test TOML serialization
        let config = crate::config::Config {
            typing_speed: TypingSpeed::Fast,
            left_click_paste: true,
        };

        let toml = toml::to_string(&config).unwrap();
        assert!(toml.contains("typing_speed = \"fast\""));
        assert!(toml.contains("left_click_paste = true"));
    }
}
