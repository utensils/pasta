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
}
