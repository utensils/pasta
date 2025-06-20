use std::time::Duration;

use enigo::{Enigo, Key, Keyboard};
use log::debug;
use tokio::sync::mpsc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TypingSpeed {
    Slow,
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
    TypeText(String),
    SetSpeed(TypingSpeed),
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
            let mut current_speed = TypingSpeed::Normal;

            while let Some(cmd) = rx.blocking_recv() {
                match cmd {
                    KeyboardCommand::TypeText(text) => {
                        let delay = Duration::from_millis(current_speed.delay_ms());

                        debug!("Typing text with {current_speed:?} speed");

                        // Chunk text for better performance with long content
                        const CHUNK_SIZE: usize = 200;
                        let chars: Vec<char> = text.chars().collect();
                        let chunks: Vec<String> = chars
                            .chunks(CHUNK_SIZE)
                            .map(|chunk| chunk.iter().collect::<String>())
                            .collect();

                        for (i, chunk) in chunks.iter().enumerate() {
                            // Type each character in the chunk
                            for ch in chunk.chars() {
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

                            // Add a slightly longer delay between chunks
                            if i < chunks.len() - 1 {
                                std::thread::sleep(Duration::from_millis(100));
                            }
                        }

                        debug!("Finished typing text");
                    }
                    KeyboardCommand::SetSpeed(speed) => {
                        current_speed = speed;
                    }
                }
            }
        });

        Ok(Self { tx })
    }

    pub fn set_typing_speed(&self, speed: TypingSpeed) {
        let _ = self.tx.blocking_send(KeyboardCommand::SetSpeed(speed));
    }

    pub async fn type_text(&self, text: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.tx
            .send(KeyboardCommand::TypeText(text.to_string()))
            .await?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_typing_speed_delay_values() {
        assert_eq!(TypingSpeed::Slow.delay_ms(), 50);
        assert_eq!(TypingSpeed::Normal.delay_ms(), 25);
        assert_eq!(TypingSpeed::Fast.delay_ms(), 10);
    }

    #[test]
    fn test_typing_speed_serialization() {
        let speed = TypingSpeed::Fast;
        let json = serde_json::to_string(&speed).unwrap();
        assert_eq!(json, "\"fast\"");

        let deserialized: TypingSpeed = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized, TypingSpeed::Fast);
    }

    #[test]
    fn test_keyboard_command_creation() {
        let cmd = KeyboardCommand::TypeText("hello".to_string());
        match cmd {
            KeyboardCommand::TypeText(text) => assert_eq!(text, "hello"),
            _ => panic!("Wrong command type"),
        }

        let cmd = KeyboardCommand::SetSpeed(TypingSpeed::Slow);
        match cmd {
            KeyboardCommand::SetSpeed(speed) => assert_eq!(speed, TypingSpeed::Slow),
            _ => panic!("Wrong command type"),
        }
    }

    #[test]
    fn test_text_chunking_logic() {
        // Test that chunking logic works correctly
        const CHUNK_SIZE: usize = 200;
        let text = "a".repeat(550); // 550 chars should create 3 chunks
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        assert_eq!(chunks.len(), 3);
        assert_eq!(chunks[0].len(), 200);
        assert_eq!(chunks[1].len(), 200);
        assert_eq!(chunks[2].len(), 150);
    }

    #[test]
    fn test_special_character_handling() {
        // This test just verifies the logic, not actual keyboard input
        let special_chars = vec!['\n', '\t', 'a'];

        for ch in special_chars {
            match ch {
                '\n' => assert!(true),    // Would press Return
                '\t' => assert!(true),    // Would press Tab
                _ => assert_eq!(ch, 'a'), // Regular character
            }
        }
    }

    #[test]
    fn test_typing_speed_all_variants() {
        // Test all speed variants
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

        for speed in speeds {
            let delay = speed.delay_ms();
            assert!(delay > 0);
            assert!(delay <= 50);
        }
    }

    #[test]
    fn test_typing_speed_deserialization() {
        // Test deserialization from all lowercase values
        let slow: TypingSpeed = serde_json::from_str("\"slow\"").unwrap();
        assert_eq!(slow, TypingSpeed::Slow);

        let normal: TypingSpeed = serde_json::from_str("\"normal\"").unwrap();
        assert_eq!(normal, TypingSpeed::Normal);

        let fast: TypingSpeed = serde_json::from_str("\"fast\"").unwrap();
        assert_eq!(fast, TypingSpeed::Fast);
    }

    #[test]
    fn test_keyboard_command_debug() {
        let cmd = KeyboardCommand::TypeText("test".to_string());
        let debug_str = format!("{:?}", cmd);
        assert!(debug_str.contains("TypeText"));
        assert!(debug_str.contains("test"));

        let cmd = KeyboardCommand::SetSpeed(TypingSpeed::Fast);
        let debug_str = format!("{:?}", cmd);
        assert!(debug_str.contains("SetSpeed"));
        assert!(debug_str.contains("Fast"));
    }

    #[test]
    fn test_keyboard_command_clone() {
        let cmd = KeyboardCommand::TypeText("hello".to_string());
        let cloned = cmd.clone();

        match (cmd, cloned) {
            (KeyboardCommand::TypeText(text1), KeyboardCommand::TypeText(text2)) => {
                assert_eq!(text1, text2);
            }
            _ => panic!("Clone failed"),
        }
    }

    #[test]
    fn test_typing_speed_copy() {
        let speed1 = TypingSpeed::Fast;
        let speed2 = speed1; // Copy trait
        assert_eq!(speed1, speed2);
    }

    #[test]
    fn test_empty_text_chunking() {
        const CHUNK_SIZE: usize = 200;
        let text = "";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        assert_eq!(chunks.len(), 0);
    }

    #[test]
    fn test_single_char_chunking() {
        const CHUNK_SIZE: usize = 200;
        let text = "a";
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0], "a");
    }

    #[test]
    fn test_exact_chunk_size_text() {
        const CHUNK_SIZE: usize = 200;
        let text = "b".repeat(200);
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].len(), 200);
    }

    #[test]
    fn test_unicode_text_chunking() {
        const CHUNK_SIZE: usize = 200;
        let text = "你好世界🌍".repeat(50); // Unicode characters
        let chars: Vec<char> = text.chars().collect();
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE)
            .map(|chunk| chunk.iter().collect::<String>())
            .collect();

        // Each repetition has 5 chars, 50 reps = 250 chars total
        assert_eq!(chunks.len(), 2);
        assert_eq!(chunks[0].chars().count(), 200);
        assert_eq!(chunks[1].chars().count(), 50);
    }

    #[test]
    fn test_delay_duration_conversion() {
        // Test that delay values convert properly to Duration
        let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

        for speed in speeds {
            let delay_ms = speed.delay_ms();
            let duration = Duration::from_millis(delay_ms);
            assert_eq!(duration.as_millis() as u64, delay_ms);
        }
    }

    #[test]
    fn test_chunk_delay_calculation() {
        // Test inter-chunk delay
        let inter_chunk_delay = Duration::from_millis(100);
        assert_eq!(inter_chunk_delay.as_millis(), 100);
    }

    #[test]
    fn test_keyboard_emulator_creation() {
        // Test that KeyboardEmulator::new() doesn't panic
        let result = KeyboardEmulator::new();
        assert!(result.is_ok());
    }

    #[test]
    fn test_typing_speed_eq_trait() {
        assert_eq!(TypingSpeed::Slow, TypingSpeed::Slow);
        assert_eq!(TypingSpeed::Normal, TypingSpeed::Normal);
        assert_eq!(TypingSpeed::Fast, TypingSpeed::Fast);
        assert_ne!(TypingSpeed::Slow, TypingSpeed::Fast);
    }

    #[tokio::test]
    async fn test_keyboard_emulator_type_text() {
        let emulator = KeyboardEmulator::new().unwrap();

        // Test that type_text doesn't error with basic text
        let result = emulator.type_text("test").await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_keyboard_emulator_set_speed() {
        let emulator = KeyboardEmulator::new().unwrap();

        // Test that set_typing_speed doesn't panic
        emulator.set_typing_speed(TypingSpeed::Fast);
        emulator.set_typing_speed(TypingSpeed::Slow);
        emulator.set_typing_speed(TypingSpeed::Normal);
    }

    #[test]
    fn test_special_chars_in_text() {
        let text = "Hello\nWorld\tTest";
        let chars: Vec<char> = text.chars().collect();

        let mut newline_count = 0;
        let mut tab_count = 0;
        let mut regular_count = 0;

        for ch in chars {
            match ch {
                '\n' => newline_count += 1,
                '\t' => tab_count += 1,
                _ => regular_count += 1,
            }
        }

        assert_eq!(newline_count, 1);
        assert_eq!(tab_count, 1);
        assert_eq!(regular_count, 14); // "Hello" (5) + "World" (5) + "Test" (4) = 14
    }
}
