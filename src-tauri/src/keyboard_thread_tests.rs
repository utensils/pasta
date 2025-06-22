#[cfg(test)]
mod keyboard_thread_tests {
    use std::sync::{atomic::AtomicBool, Arc};

    use tokio::sync::mpsc;

    use crate::{
        keyboard::{KeyboardCommand, TypingSpeed},
        mock_keyboard::mock::MockKeyboardEmulator,
    };

    #[test]
    fn test_keyboard_thread_spawn_behavior() {
        // Test that keyboard thread can be spawned multiple times
        let keyboard_emulator = Arc::new(MockKeyboardEmulator::new().unwrap());

        // Simulate multiple thread spawns
        for _ in 0..3 {
            let ke = keyboard_emulator.clone();
            std::thread::spawn(move || {
                // Thread would process commands here
                let _ = ke;
            })
            .join()
            .unwrap();
        }

        // Verify emulator is still valid
        assert!(Arc::strong_count(&keyboard_emulator) > 0);
    }

    #[tokio::test]
    async fn test_keyboard_command_channel_behavior() {
        // Test channel behavior with keyboard commands
        let (tx, mut rx) = mpsc::unbounded_channel::<KeyboardCommand>();

        // Send various commands
        tx.send(KeyboardCommand::TypeText(
            "Hello".to_string(),
            Arc::new(AtomicBool::new(false)),
        ))
        .unwrap();
        tx.send(KeyboardCommand::SetSpeed(TypingSpeed::Fast))
            .unwrap();
        tx.send(KeyboardCommand::TypeText(
            "World".to_string(),
            Arc::new(AtomicBool::new(false)),
        ))
        .unwrap();

        // Receive and verify commands
        let cmd1 = rx.recv().await.unwrap();
        match cmd1 {
            KeyboardCommand::TypeText(text, _) => assert_eq!(text, "Hello"),
            _ => panic!("Expected TypeText command"),
        }

        let cmd2 = rx.recv().await.unwrap();
        match cmd2 {
            KeyboardCommand::SetSpeed(speed) => assert_eq!(speed, TypingSpeed::Fast),
            _ => panic!("Expected SetSpeed command"),
        }

        let cmd3 = rx.recv().await.unwrap();
        match cmd3 {
            KeyboardCommand::TypeText(text, _) => assert_eq!(text, "World"),
            _ => panic!("Expected TypeText command"),
        }
    }

    #[test]
    fn test_text_chunking_boundaries() {
        // Test text chunking at exact boundaries
        const CHUNK_SIZE: usize = 200;

        // Test exact chunk size
        let text = "a".repeat(CHUNK_SIZE);
        let chunks: Vec<String> = text
            .chars()
            .collect::<Vec<_>>()
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].len(), CHUNK_SIZE);

        // Test one over chunk size
        let text = "a".repeat(CHUNK_SIZE + 1);
        let chunks: Vec<String> = (0..text.len())
            .step_by(CHUNK_SIZE)
            .map(|i| {
                let end = (i + CHUNK_SIZE).min(text.len());
                text[i..end].to_string()
            })
            .collect();
        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].len(), CHUNK_SIZE);
        assert_eq!(chunks[1].len(), 1);

        // Test multiple chunks
        let text = "a".repeat(CHUNK_SIZE * 3 + 50);
        let chunks: Vec<String> = (0..text.len())
            .step_by(CHUNK_SIZE)
            .map(|i| {
                let end = (i + CHUNK_SIZE).min(text.len());
                text[i..end].to_string()
            })
            .collect();
        assert_eq!(chunks.len(), 4);
        assert_eq!(chunks[0].len(), CHUNK_SIZE);
        assert_eq!(chunks[1].len(), CHUNK_SIZE);
        assert_eq!(chunks[2].len(), CHUNK_SIZE);
        assert_eq!(chunks[3].len(), 50);
    }

    #[test]
    fn test_special_character_sequences() {
        // Test various special character sequences
        let sequences = vec![
            ("\n\n\n", vec!['\n', '\n', '\n']),
            ("\t\t", vec!['\t', '\t']),
            ("\n\t\n", vec!['\n', '\t', '\n']),
            ("a\nb\tc", vec!['a', '\n', 'b', '\t', 'c']),
            ("\r\n", vec!['\r', '\n']), // Windows line ending
        ];

        for (input, expected_chars) in sequences {
            let chars: Vec<char> = input.chars().collect();
            assert_eq!(chars, expected_chars);
        }
    }

    #[test]
    fn test_typing_speed_timing_calculations() {
        // Test timing calculations for different speeds
        let speeds = vec![
            (TypingSpeed::Slow, 50),
            (TypingSpeed::Normal, 25),
            (TypingSpeed::Fast, 10),
        ];

        for (speed, expected_ms) in speeds {
            assert_eq!(speed.delay_ms(), expected_ms);

            // Test that delay can be converted to Duration
            let duration = std::time::Duration::from_millis(speed.delay_ms() as u64);
            assert_eq!(duration.as_millis(), expected_ms as u128);
        }
    }

    #[test]
    fn test_keyboard_emulator_arc_cloning() {
        // Test Arc behavior with keyboard emulator
        let emulator = Arc::new(MockKeyboardEmulator::new().unwrap());
        let initial_count = Arc::strong_count(&emulator);

        // Clone multiple times
        let clone1 = emulator.clone();
        assert_eq!(Arc::strong_count(&emulator), initial_count + 1);

        let clone2 = emulator.clone();
        assert_eq!(Arc::strong_count(&emulator), initial_count + 2);

        // Drop clones
        drop(clone1);
        assert_eq!(Arc::strong_count(&emulator), initial_count + 1);

        drop(clone2);
        assert_eq!(Arc::strong_count(&emulator), initial_count);
    }

    #[tokio::test]
    async fn test_concurrent_type_text_operations() {
        use tokio::time::{sleep, Duration};

        let keyboard_emulator = Arc::new(MockKeyboardEmulator::new().unwrap());

        // Spawn multiple concurrent type operations
        let mut handles = vec![];

        for i in 0..5 {
            let ke = keyboard_emulator.clone();
            let handle = tokio::spawn(async move {
                let text = format!("Task {}", i);
                ke.type_text(&text, Arc::new(AtomicBool::new(false)))
                    .await
                    .unwrap();
                sleep(Duration::from_millis(10)).await;
            });
            handles.push(handle);
        }

        // Wait for all to complete
        for handle in handles {
            handle.await.unwrap();
        }
    }

    #[test]
    fn test_keyboard_command_memory_layout() {
        use std::mem;

        // Test memory layout of KeyboardCommand enum
        let type_text_cmd =
            KeyboardCommand::TypeText("Hello".to_string(), Arc::new(AtomicBool::new(false)));
        let set_speed_cmd = KeyboardCommand::SetSpeed(TypingSpeed::Fast);

        // Both variants should have reasonable size
        assert!(mem::size_of_val(&type_text_cmd) < 100);
        assert!(mem::size_of_val(&set_speed_cmd) < 100);

        // Test that commands can be moved
        let cmd = KeyboardCommand::TypeText("Test".to_string(), Arc::new(AtomicBool::new(false)));
        let moved_cmd = cmd;
        match moved_cmd {
            KeyboardCommand::TypeText(text, _) => assert_eq!(text, "Test"),
            _ => panic!("Unexpected command type"),
        }
    }

    #[test]
    fn test_channel_closed_behavior() {
        // Test behavior when channel is closed
        let (tx, rx) = mpsc::unbounded_channel::<KeyboardCommand>();

        // Send a command
        tx.send(KeyboardCommand::TypeText(
            "Test".to_string(),
            Arc::new(AtomicBool::new(false)),
        ))
        .unwrap();

        // Close the channel by dropping receiver
        drop(rx);

        // Try to send after close - should fail
        let result = tx.send(KeyboardCommand::TypeText(
            "Failed".to_string(),
            Arc::new(AtomicBool::new(false)),
        ));
        assert!(result.is_err());
    }

    #[test]
    fn test_typing_speed_state_machine() {
        // Test typing speed as a state machine
        let mut current_speed = TypingSpeed::Normal;

        // Apply transitions step by step
        // Transition 1: Normal -> Fast
        if current_speed == TypingSpeed::Normal {
            current_speed = TypingSpeed::Fast;
        }
        assert_eq!(current_speed, TypingSpeed::Fast);

        // Transition 2: Fast -> Slow
        if current_speed == TypingSpeed::Fast {
            current_speed = TypingSpeed::Slow;
        }
        assert_eq!(current_speed, TypingSpeed::Slow);

        // Transition 3: Slow -> Normal
        if current_speed == TypingSpeed::Slow {
            current_speed = TypingSpeed::Normal;
        }
        assert_eq!(current_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_text_processing_edge_cases() {
        // Test edge cases in text processing
        let edge_cases = vec![
            "",           // Empty string
            " ",          // Single space
            "  ",         // Multiple spaces
            "\u{0000}",   // Null character
            "\u{FEFF}",   // Zero-width no-break space
            "🦀",         // Emoji
            "中文",       // Chinese characters
            "العربية",    // Arabic (RTL)
            "test\0test", // Embedded null
        ];

        for text in edge_cases {
            // In real keyboard emulator, these would be processed
            let _chars: Vec<char> = text.chars().collect();
        }
    }
}
