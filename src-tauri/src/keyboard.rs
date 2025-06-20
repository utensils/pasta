use enigo::{Enigo, Key, Keyboard};
use log::debug;
use std::time::Duration;
use tokio::sync::mpsc;

#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
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
                        
                        debug!("Typing text with {:?} speed", current_speed);
                        
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
        self.tx.send(KeyboardCommand::TypeText(text.to_string())).await?;
        Ok(())
    }
}