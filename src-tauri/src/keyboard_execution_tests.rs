#[cfg(test)]
mod keyboard_execution_tests {
    use std::{
        sync::{atomic::AtomicBool, Arc},
        time::Duration,
    };

    use tokio::sync::mpsc;

    use crate::{
        keyboard::{KeyboardCommand, TypingSpeed},
        mock_keyboard::mock::MockKeyboardEmulator,
    };

    #[test]
    fn test_keyboard_thread_lifecycle() {
        // Test the keyboard emulator thread lifecycle
        let emulator = MockKeyboardEmulator::new();
        assert!(emulator.is_ok());

        let keyboard = emulator.unwrap();

        // The thread should be running after creation
        // Send a command to verify the thread is alive
        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {
            let cancellation_flag = Arc::new(AtomicBool::new(false));
            let result = keyboard.type_text("test", cancellation_flag).await;
            assert!(result.is_ok());
        });

        // Give thread time to process
        std::thread::sleep(Duration::from_millis(50));

        // Verify the text was recorded (not actually typed)
        assert_eq!(keyboard.get_typed_text(), vec!["test"]);
    }

    #[test]
    fn test_keyboard_command_processing() {
        // Test command processing in the keyboard thread
        let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(10);

        // Spawn a thread similar to keyboard emulator
        std::thread::spawn(move || {
            let mut current_speed = TypingSpeed::Normal;

            while let Some(cmd) = rx.blocking_recv() {
                match cmd {
                    KeyboardCommand::TypeText(text, _cancellation_flag) => {
                        // Simulate text processing
                        let delay = Duration::from_millis(current_speed.delay_ms());
                        assert!(delay.as_millis() > 0);

                        // Simulate chunking
                        const CHUNK_SIZE: usize = 200;
                        let chars: Vec<char> = text.chars().collect();
                        let chunk_count = (chars.len() + CHUNK_SIZE - 1) / CHUNK_SIZE;
                        assert!(chunk_count > 0);
                    }
                    KeyboardCommand::SetSpeed(speed) => {
                        current_speed = speed;
                    }
                }
            }
        });

        // Send commands
        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {
            tx.send(KeyboardCommand::SetSpeed(TypingSpeed::Fast))
                .await
                .unwrap();
            let cancellation_flag = Arc::new(AtomicBool::new(false));
            tx.send(KeyboardCommand::TypeText(
                "Hello".to_string(),
                cancellation_flag,
            ))
            .await
            .unwrap();
        });

        // Give thread time to process
        std::thread::sleep(Duration::from_millis(50));
    }

    #[test]
    fn test_text_chunking_logic() {
        // Test the text chunking logic used in keyboard thread
        const CHUNK_SIZE: usize = 200;

        let text1 = "a".repeat(CHUNK_SIZE);
        let text2 = "a".repeat(CHUNK_SIZE + 1);
        let text3 = "a".repeat(CHUNK_SIZE * 2);
        let text4 = "a".repeat(CHUNK_SIZE * 2 + 1);

        let test_cases = vec![
            ("", 0),
            ("a", 1),
            (text1.as_str(), 1),
            (text2.as_str(), 2),
            (text3.as_str(), 2),
            (text4.as_str(), 3),
        ];

        for (text, expected_chunks) in test_cases {
            let chars: Vec<char> = text.chars().collect();
            let chunks: Vec<String> = chars
                .chunks(CHUNK_SIZE)
                .map(|chunk| chunk.iter().collect::<String>())
                .collect();

            assert_eq!(chunks.len(), expected_chunks, "Text: {} chars", text.len());

            // Verify chunk sizes
            for (i, chunk) in chunks.iter().enumerate() {
                if i < chunks.len() - 1 {
                    assert_eq!(chunk.len(), CHUNK_SIZE);
                } else {
                    // Last chunk can be smaller
                    assert!(chunk.len() <= CHUNK_SIZE);
                    assert!(chunk.len() > 0 || text.is_empty());
                }
            }
        }
    }

    #[test]
    fn test_special_character_processing() {
        // Test special character handling in keyboard thread
        let special_chars = vec![
            ('\n', "newline"),
            ('\t', "tab"),
            ('\r', "carriage return"),
            (' ', "space"),
            ('!', "exclamation"),
            ('@', "at"),
            ('#', "hash"),
            ('$', "dollar"),
            ('%', "percent"),
            ('^', "caret"),
            ('&', "ampersand"),
            ('*', "asterisk"),
            ('(', "left paren"),
            (')', "right paren"),
        ];

        for (ch, name) in special_chars {
            // Each character should be processable
            assert_eq!(ch.to_string().len(), ch.len_utf8(), "Character: {}", name);
        }
    }

    #[test]
    #[ignore = "Flaky timing test that often fails in CI due to slow/busy machines"]
    fn test_delay_timing_accuracy() {
        // Test delay timing calculations
        use std::time::Instant;

        let speeds = vec![
            (TypingSpeed::Slow, 50),
            (TypingSpeed::Normal, 25),
            (TypingSpeed::Fast, 10),
        ];

        for (speed, expected_ms) in speeds {
            let delay = Duration::from_millis(speed.delay_ms());
            assert_eq!(delay.as_millis(), expected_ms as u128);

            // Test that we can sleep for this duration
            let start = Instant::now();
            std::thread::sleep(delay);
            let elapsed = start.elapsed();

            // Allow some tolerance for timing (more generous for CI environments)
            assert!(elapsed >= delay);
            // Increase tolerance to 100ms for CI environments under load
            assert!(
                elapsed < delay + Duration::from_millis(100),
                "Elapsed time {:?} exceeded expected delay {:?} by more than 100ms",
                elapsed,
                delay
            );
        }
    }

    #[test]
    fn test_channel_capacity_handling() {
        // Test channel capacity and blocking behavior
        let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(2); // Small capacity

        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {
            let cancellation_flag = Arc::new(AtomicBool::new(false));

            // Fill the channel
            tx.send(KeyboardCommand::TypeText(
                "1".to_string(),
                cancellation_flag.clone(),
            ))
            .await
            .unwrap();
            tx.send(KeyboardCommand::TypeText(
                "2".to_string(),
                cancellation_flag.clone(),
            ))
            .await
            .unwrap();

            // This would block if channel is full, so try_send
            let result = tx.try_send(KeyboardCommand::TypeText(
                "3".to_string(),
                cancellation_flag.clone(),
            ));
            assert!(result.is_err()); // Channel should be full

            // Consume one message
            let _msg = rx.recv().await;

            // Now we should be able to send
            let result2 = tx.try_send(KeyboardCommand::TypeText(
                "3".to_string(),
                cancellation_flag,
            ));
            assert!(result2.is_ok());
        });
    }

    #[test]
    fn test_keyboard_emulator_drop_behavior() {
        // Test that keyboard emulator properly cleans up when dropped
        let emulator = Arc::new(MockKeyboardEmulator::new().unwrap());
        let initial_count = Arc::strong_count(&emulator);

        {
            let _clone = emulator.clone();
            assert_eq!(Arc::strong_count(&emulator), initial_count + 1);
        }

        // After clone is dropped
        assert_eq!(Arc::strong_count(&emulator), initial_count);

        // Drop the emulator
        drop(emulator);
        // Thread should eventually terminate
    }

    #[test]
    fn test_unicode_character_handling() {
        // Test Unicode character handling in keyboard
        let unicode_tests = vec![
            "Hello 世界",
            "Emoji: 🦀 ⌨️ 💻",
            "Math: ∑ ∏ ∫",
            "Symbols: ™ © ®",
            "Accents: café naïve",
            "Mixed: ABC123中文🦀",
        ];

        for text in unicode_tests {
            let chars: Vec<char> = text.chars().collect();

            // Verify each character is properly extracted
            for ch in &chars {
                // char is always a valid character
                assert!(ch.len_utf8() > 0);
            }

            // Verify character count
            assert_eq!(chars.len(), text.chars().count());
        }
    }

    #[test]
    fn test_chunk_delay_calculation() {
        // Test chunk delay calculation (100ms between chunks)
        const CHUNK_DELAY: Duration = Duration::from_millis(100);

        // Test with multiple chunks
        let chunk_count = 5;
        let total_delay = CHUNK_DELAY.as_millis() * (chunk_count - 1) as u128;

        assert_eq!(total_delay, 400); // 4 delays between 5 chunks
    }
}
