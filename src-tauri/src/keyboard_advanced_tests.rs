#[cfg(test)]
mod keyboard_advanced_tests {
    use std::{
        sync::Arc,
        time::Duration,
    };

    use tokio::sync::mpsc;

    use crate::{
        keyboard::{KeyboardCommand, TypingSpeed},
        mock_keyboard::mock::MockKeyboardEmulator,
    };

    #[test]
    fn test_keyboard_emulator_creation_multiple() {
        // Test creating multiple keyboard emulators
        let emulators: Vec<_> = (0..5).map(|_| MockKeyboardEmulator::new()).collect();

        for (i, emulator) in emulators.iter().enumerate() {
            assert!(emulator.is_ok(), "Emulator {} creation failed", i);
        }
    }

    #[test]
    fn test_typing_speed_delay_values() {
        // Verify exact delay values
        assert_eq!(TypingSpeed::Slow.delay_ms(), 50);
        assert_eq!(TypingSpeed::Normal.delay_ms(), 25);
        assert_eq!(TypingSpeed::Fast.delay_ms(), 10);

        // Test all combinations
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        let expected_delays = vec![50, 25, 10];

        for (speed, expected) in speeds.iter().zip(expected_delays.iter()) {
            assert_eq!(speed.delay_ms(), *expected);
        }
    }

    #[test]
    fn test_keyboard_thread_command_ordering() {
        // Test that commands are processed in order
        let (tx, mut rx) = mpsc::unbounded_channel::<KeyboardCommand>();

        // Send commands in specific order
        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {
            tx.send(KeyboardCommand::SetSpeed(TypingSpeed::Fast))
                .unwrap();
            tx.send(KeyboardCommand::TypeText("First".to_string()))
                .unwrap();
            tx.send(KeyboardCommand::SetSpeed(TypingSpeed::Slow))
                .unwrap();
            tx.send(KeyboardCommand::TypeText("Second".to_string()))
                .unwrap();
        });

        // Verify order
        let mut commands = Vec::new();
        while let Ok(cmd) = rx.try_recv() {
            commands.push(cmd);
        }

        assert_eq!(commands.len(), 4);
        match &commands[0] {
            KeyboardCommand::SetSpeed(speed) => assert_eq!(*speed, TypingSpeed::Fast),
            _ => panic!("Expected SetSpeed command"),
        }
        match &commands[1] {
            KeyboardCommand::TypeText(text) => assert_eq!(text, "First"),
            _ => panic!("Expected TypeText command"),
        }
    }

    #[tokio::test]
    async fn test_keyboard_emulator_concurrent_operations() {
        let emulator = Arc::new(MockKeyboardEmulator::new().unwrap());

        // Spawn multiple concurrent operations
        let mut handles = vec![];

        for i in 0..5 {
            let emulator_clone = emulator.clone();
            let handle = tokio::spawn(async move {
                if i % 2 == 0 {
                    emulator_clone.set_typing_speed(TypingSpeed::Fast);
                } else {
                    let _ = emulator_clone.type_text(&format!("Test {}", i)).await;
                }
            });
            handles.push(handle);
        }

        // Wait for all operations
        for handle in handles {
            handle.await.unwrap();
        }
    }

    #[test]
    fn test_text_chunking_edge_cases() {
        const CHUNK_SIZE: usize = 200;

        // Test exact chunk boundary
        let text = "a".repeat(CHUNK_SIZE);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<_> = chars.chunks(CHUNK_SIZE).collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].len(), CHUNK_SIZE);

        // Test one over chunk boundary
        let text = "a".repeat(CHUNK_SIZE + 1);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<_> = chars.chunks(CHUNK_SIZE).collect();
        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].len(), CHUNK_SIZE);
        assert_eq!(chunks[1].len(), 1);

        // Test empty text
        let text = "";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<_> = chars.chunks(CHUNK_SIZE).collect();
        assert_eq!(chunks.len(), 0);

        // Test single character
        let text = "x";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<_> = chars.chunks(CHUNK_SIZE).collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].len(), 1);
    }

    #[test]
    fn test_unicode_text_chunking() {
        const CHUNK_SIZE: usize = 200;

        // Test with various Unicode characters
        let unicode_texts = vec![
            "🦀".repeat(CHUNK_SIZE),
            "中文测试".repeat(50),
            "café".repeat(40),
            "Здравствуйте".repeat(15),
            "🦀⌨️💻".repeat(66),
        ];

        for text in unicode_texts {
            let chars: Vec<char> = text.chars().collect();
            let chunks: Vec<_> = chars.chunks(CHUNK_SIZE).collect();

            // Verify chunk count
            let expected_chunks = (chars.len() + CHUNK_SIZE - 1) / CHUNK_SIZE;
            assert_eq!(chunks.len(), expected_chunks);

            // Verify no characters are lost
            let reconstructed: String = chunks.iter().flat_map(|chunk| chunk.iter()).collect();
            assert_eq!(reconstructed, text);
        }
    }

    #[test]
    fn test_special_character_handling() {
        // Test various special characters
        let special_texts = vec![
            "\n\n\n",
            "\t\t\t",
            "\r\n",
            "Line 1\nLine 2\nLine 3",
            "Tab\tSeparated\tValues",
            "Mixed\n\t\r\nSpecial",
            "Quotes: \"'`",
            "Symbols: !@#$%^&*()",
            "Math: +-*/=<>",
            "Brackets: ()[]{}<>",
        ];

        for text in special_texts {
            // Verify each character is valid
            for ch in text.chars() {
                assert!(ch.len_utf8() > 0);

                // Test character categorization
                let is_special = matches!(ch, '\n' | '\t' | '\r');
                if is_special {
                    assert!(ch.is_control());
                }
            }
        }
    }

    #[test]
    fn test_keyboard_command_memory_size() {
        // Test memory efficiency of commands
        use std::mem;

        let small_text_cmd = KeyboardCommand::TypeText("Hi".to_string());
        let large_text_cmd = KeyboardCommand::TypeText("x".repeat(10000));
        let speed_cmd = KeyboardCommand::SetSpeed(TypingSpeed::Fast);

        // Speed command should be small
        assert!(mem::size_of_val(&speed_cmd) < 100);

        // Note: With enums, all variants have the same size (size of largest variant)
        // So we test the string sizes instead
        match (&small_text_cmd, &large_text_cmd) {
            (KeyboardCommand::TypeText(small), KeyboardCommand::TypeText(large)) => {
                assert!(small.len() < large.len());
            }
            _ => panic!("Expected TypeText commands"),
        }
    }

    #[tokio::test]
    async fn test_keyboard_emulator_error_recovery() {
        let emulator = MockKeyboardEmulator::new().unwrap();

        // Test with various problematic inputs
        let long_string = "a".repeat(1_000_000);
        let test_cases = vec![
            "",                   // Empty string
            " ",                  // Single space
            "\0",                 // Null character
            long_string.as_str(), // Very long string
        ];

        for (i, text) in test_cases.iter().enumerate() {
            let result = emulator.type_text(text).await;
            assert!(result.is_ok(), "Test case {} failed", i);
        }
    }

    #[test]
    fn test_typing_speed_transitions() {
        let emulator = MockKeyboardEmulator::new().unwrap();

        // Test all possible speed transitions
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

        for from_speed in &speeds {
            for to_speed in &speeds {
                emulator.set_typing_speed(*from_speed);
                emulator.set_typing_speed(*to_speed);
                // Verify transition doesn't cause issues
            }
        }
    }

    #[test]
    fn test_keyboard_channel_closure() {
        // Test channel behavior when sender is dropped
        let (tx, mut rx) = mpsc::unbounded_channel::<KeyboardCommand>();

        // Send some commands
        tx.send(KeyboardCommand::TypeText("Test".to_string()))
            .unwrap();

        // Drop sender
        drop(tx);

        // Receiver should get the message then None
        assert!(rx.try_recv().is_ok());
        assert!(rx.try_recv().is_err());
    }

    #[test]
    fn test_chunk_delay_timing() {
        // Test chunk delay calculations
        const CHUNK_DELAY_MS: u64 = 100;

        let chunk_counts: Vec<u64> = vec![1, 2, 5, 10, 100];

        for count in chunk_counts {
            let total_delay_ms = CHUNK_DELAY_MS * count.saturating_sub(1);
            let total_delay = Duration::from_millis(total_delay_ms);

            // Verify delay calculation
            assert_eq!(total_delay.as_millis(), total_delay_ms as u128);
        }
    }

    #[test]
    fn test_keyboard_state_isolation() {
        // Test that multiple emulators have isolated state
        let emulator1 = Arc::new(MockKeyboardEmulator::new().unwrap());
        let emulator2 = Arc::new(MockKeyboardEmulator::new().unwrap());

        // Set different speeds
        emulator1.set_typing_speed(TypingSpeed::Fast);
        emulator2.set_typing_speed(TypingSpeed::Slow);

        // Each should maintain its own state
        // (We can't directly verify internal state, but this ensures no panic)
    }

    #[tokio::test]
    async fn test_keyboard_rapid_commands() {
        let emulator = MockKeyboardEmulator::new().unwrap();

        // Send many commands rapidly
        for i in 0..50 {
            if i % 10 == 0 {
                emulator.set_typing_speed(TypingSpeed::Fast);
            }
            let _ = emulator.type_text(&format!("{}", i)).await;
        }
    }
}
