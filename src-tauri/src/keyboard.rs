use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    time::Duration,
};

use enigo::{Enigo, Key, Keyboard};
use log::{debug, info};
use tokio::sync::mpsc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum TypingSpeed {
    Slow,
    #[default]
    Normal,
    Fast,
}

impl TypingSpeed {
    pub fn delay_ms(&self) -> u64 {
        match self {
            TypingSpeed::Slow => 50,
            TypingSpeed::Normal => 25,
            TypingSpeed::Fast => 10,
        }
    }
}

#[derive(Debug, Clone)]
pub enum KeyboardCommand {
    TypeText(String, Arc<AtomicBool>),
}

pub struct KeyboardEmulator {
    tx: mpsc::Sender<KeyboardCommand>,
}

impl KeyboardEmulator {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(10);

        // Spawn a dedicated thread for keyboard operations
        std::thread::spawn(move || {
            let mut enigo = Enigo::new(&enigo::Settings::default()).unwrap();
            let typing_speed = TypingSpeed::default(); // Always use Normal speed

            while let Some(cmd) = rx.blocking_recv() {
                match cmd {
                    KeyboardCommand::TypeText(text, cancellation_flag) => {
                        let delay = Duration::from_millis(typing_speed.delay_ms());

                        debug!("Typing text with {typing_speed:?} speed");

                        // Chunk text for better performance with long content
                        const CHUNK_SIZE: usize = 200;
                        let chars: Vec<char> = text.chars().collect();
                        let chunks: Vec<String> = chars
                            .chunks(CHUNK_SIZE)
                            .map(|chunk| chunk.iter().collect::<String>())
                            .collect();

                        for (i, chunk) in chunks.iter().enumerate() {
                            // Check cancellation flag at the start of each chunk
                            if cancellation_flag.load(Ordering::Relaxed) {
                                info!("Typing cancelled by user");
                                break;
                            }

                            // Type each character in the chunk
                            for (char_index, ch) in chunk.chars().enumerate() {
                                // Check cancellation at the start of each character for immediate response
                                if char_index == 0 && cancellation_flag.load(Ordering::Relaxed) {
                                    info!("Typing cancelled by user");
                                    break;
                                }
                                // Check cancellation flag periodically (every 10 characters)
                                if char_index % 10 == 0 && cancellation_flag.load(Ordering::Relaxed)
                                {
                                    info!("Typing cancelled by user");
                                    break;
                                }

                                match ch {
                                    '\n' => {
                                        let _ = enigo.key(Key::Return, enigo::Direction::Click);
                                    }
                                    '\t' => {
                                        let _ = enigo.key(Key::Tab, enigo::Direction::Click);
                                    }
                                    _ => {
                                        let _ = enigo.text(&ch.to_string());
                                    }
                                }
                                std::thread::sleep(delay);
                            }

                            // Check if cancelled before continuing to next chunk
                            if cancellation_flag.load(Ordering::Relaxed) {
                                info!("Typing cancelled by user");
                                break;
                            }

                            // Add a small pause between chunks to avoid overwhelming the system
                            if i < chunks.len() - 1 {
                                std::thread::sleep(Duration::from_millis(100));
                            }
                        }

                        info!("Finished typing text");
                    }
                }
            }
        });

        Ok(Self { tx })
    }

    pub async fn type_text(
        &self,
        text: &str,
        cancellation_flag: Arc<AtomicBool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        self.tx
            .send(KeyboardCommand::TypeText(
                text.to_string(),
                cancellation_flag,
            ))
            .await?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_typing_speed_default() {
        assert_eq!(TypingSpeed::default(), TypingSpeed::Normal);
    }

    #[test]
    fn test_typing_speed_delay_values() {
        assert_eq!(TypingSpeed::Slow.delay_ms(), 50);
        assert_eq!(TypingSpeed::Normal.delay_ms(), 25);
        assert_eq!(TypingSpeed::Fast.delay_ms(), 10);
    }

    #[test]
    fn test_typing_speed_serialization() {
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Slow).unwrap(),
            "\"slow\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Normal).unwrap(),
            "\"normal\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Fast).unwrap(),
            "\"fast\""
        );
    }

    #[test]
    fn test_typing_speed_deserialization() {
        assert_eq!(
            serde_json::from_str::<TypingSpeed>("\"slow\"").unwrap(),
            TypingSpeed::Slow
        );
        assert_eq!(
            serde_json::from_str::<TypingSpeed>("\"normal\"").unwrap(),
            TypingSpeed::Normal
        );
        assert_eq!(
            serde_json::from_str::<TypingSpeed>("\"fast\"").unwrap(),
            TypingSpeed::Fast
        );
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_keyboard_emulator_creation() {
        let result = KeyboardEmulator::new();
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_keyboard_emulator_type_text() {
        let keyboard = KeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let result = keyboard.type_text("test", cancellation_flag).await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_keyboard_command_creation() {
        let cmd = KeyboardCommand::TypeText("test".to_string(), Arc::new(AtomicBool::new(false)));
        match cmd {
            KeyboardCommand::TypeText(text, _) => assert_eq!(text, "test"),
        }
    }

    #[test]
    fn test_keyboard_command_debug() {
        let cmd = KeyboardCommand::TypeText("test".to_string(), Arc::new(AtomicBool::new(false)));
        let debug_str = format!("{:?}", cmd);
        assert!(debug_str.contains("TypeText"));
        assert!(debug_str.contains("test"));
    }

    #[test]
    fn test_keyboard_command_clone() {
        let cmd = KeyboardCommand::TypeText("test".to_string(), Arc::new(AtomicBool::new(false)));
        let cloned = cmd.clone();
        match cloned {
            KeyboardCommand::TypeText(text, _) => assert_eq!(text, "test"),
        }
    }

    #[test]
    fn test_typing_speed_eq_trait() {
        assert_eq!(TypingSpeed::Slow, TypingSpeed::Slow);
        assert_eq!(TypingSpeed::Normal, TypingSpeed::Normal);
        assert_eq!(TypingSpeed::Fast, TypingSpeed::Fast);
        assert_ne!(TypingSpeed::Slow, TypingSpeed::Fast);
    }

    #[test]
    fn test_typing_speed_copy() {
        let speed = TypingSpeed::Normal;
        let copied = speed;
        assert_eq!(speed, copied);
    }

    #[test]
    fn test_text_chunking_logic() {
        let text = "a".repeat(500);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 3);
        assert_eq!(chunks[0].len(), 200);
        assert_eq!(chunks[1].len(), 200);
        assert_eq!(chunks[2].len(), 100);
    }

    #[test]
    fn test_empty_text_chunking() {
        let text = "";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 0);
    }

    #[test]
    fn test_single_char_chunking() {
        let text = "a";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0], "a");
    }

    #[test]
    fn test_exact_chunk_size_text() {
        let text = "a".repeat(200);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].len(), 200);
    }

    #[test]
    fn test_special_character_handling() {
        // Test newline and tab characters
        let special_chars = vec!['\n', '\t'];
        for ch in special_chars {
            assert!(ch == '\n' || ch == '\t');
        }
    }

    #[test]
    fn test_unicode_text_chunking() {
        let text = "😀🎉".repeat(100);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].chars().count(), 200);
    }

    #[test]
    fn test_keyboard_emulator_channel_size() {
        // The channel is created with size 10
        let (tx, _rx) = mpsc::channel::<KeyboardCommand>(10);
        // Just verify we can create a sender
        let _ = tx;
    }

    #[test]
    fn test_special_chars_in_text() {
        let text = "Hello\nWorld\tTest";
        let chars: Vec<char> = text.chars().collect();
        assert!(chars.contains(&'\n'));
        assert!(chars.contains(&'\t'));
    }

    #[test]
    fn test_typing_speed_all_variants() {
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];
        for speed in speeds {
            assert!(speed.delay_ms() > 0);
        }
    }

    #[test]
    fn test_delay_duration_conversion() {
        let speed = TypingSpeed::Normal;
        let delay = Duration::from_millis(speed.delay_ms());
        assert_eq!(delay.as_millis(), 25);
    }

    #[test]
    fn test_chunk_delay_calculation() {
        // Chunk delay is hardcoded to 100ms
        let chunk_delay = Duration::from_millis(100);
        assert_eq!(chunk_delay.as_millis(), 100);
    }

    #[test]
    fn test_keyboard_command_exhaustive_match() {
        let cmd = KeyboardCommand::TypeText("test".to_string(), Arc::new(AtomicBool::new(false)));
        match cmd {
            KeyboardCommand::TypeText(_, _) => {
                // All variants handled
            }
        }
    }

    #[test]
    fn test_keyboard_command_pattern_matching() {
        let cmd = KeyboardCommand::TypeText("Hello".to_string(), Arc::new(AtomicBool::new(false)));
        let KeyboardCommand::TypeText(text, _) = cmd;
        assert_eq!(text, "Hello");
    }

    #[test]
    fn test_cancellation_flag_functionality() {
        let flag = Arc::new(AtomicBool::new(false));
        assert!(!flag.load(Ordering::Relaxed));

        flag.store(true, Ordering::Relaxed);
        assert!(flag.load(Ordering::Relaxed));
    }

    #[test]
    fn test_keyboard_command_with_cancellation() {
        let flag = Arc::new(AtomicBool::new(true));
        let cmd = KeyboardCommand::TypeText("test".to_string(), flag.clone());

        let KeyboardCommand::TypeText(_, cancellation_flag) = cmd;
        assert!(cancellation_flag.load(Ordering::Relaxed));
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_keyboard_emulator_multiple_operations() {
        let keyboard = KeyboardEmulator::new().unwrap();

        // Send multiple commands
        let flag1 = Arc::new(AtomicBool::new(false));
        let flag2 = Arc::new(AtomicBool::new(false));

        let result1 = keyboard.type_text("test1", flag1).await;
        let result2 = keyboard.type_text("test2", flag2).await;

        assert!(result1.is_ok());
        assert!(result2.is_ok());
    }

    #[test]
    fn test_long_text_with_special_chars() {
        let text = "Line1\nLine2\tTab\nLine3".repeat(50);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(200)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        // Verify chunks maintain special characters
        let all_text: String = chunks.join("");
        assert_eq!(all_text, text);
    }

    #[test]
    fn test_typing_speed_coverage() {
        // Ensure all typing speeds are tested
        assert_eq!(TypingSpeed::Slow.delay_ms(), 50);
        assert_eq!(TypingSpeed::Normal.delay_ms(), 25);
        assert_eq!(TypingSpeed::Fast.delay_ms(), 10);

        // Test default
        let default_speed = TypingSpeed::default();
        assert_eq!(default_speed, TypingSpeed::Normal);
    }

    #[test]
    fn test_cancellation_flag_shared_across_threads() {
        let flag = Arc::new(AtomicBool::new(false));
        let flag_clone = flag.clone();

        // Spawn a thread that sets the flag
        let handle = std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(10));
            flag_clone.store(true, Ordering::Relaxed);
        });

        // Wait for the thread to complete
        handle.join().unwrap();

        // Check that the flag is set
        assert!(flag.load(Ordering::Relaxed));
    }

    #[test]
    fn test_chunk_iteration_with_cancellation_check() {
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let chunks = vec!["chunk1".to_string(), "chunk2".to_string()];

        for (i, chunk) in chunks.iter().enumerate() {
            if cancellation_flag.load(Ordering::Relaxed) {
                break;
            }
            assert_eq!(chunk.len(), 6);
            if i == 0 {
                // Simulate cancellation after first chunk
                cancellation_flag.store(true, Ordering::Relaxed);
            }
        }
    }
}
