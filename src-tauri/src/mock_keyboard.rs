#[cfg(test)]
pub mod mock {
    use std::sync::{Arc, Mutex};
    use std::sync::atomic::{AtomicBool, Ordering};

    use tokio::sync::mpsc;

    use crate::keyboard::{KeyboardCommand, TypingSpeed};

    /// A mock keyboard emulator that doesn't perform actual keyboard operations
    /// Used for testing to prevent tests from typing on the system
    pub struct MockKeyboardEmulator {
        tx: mpsc::Sender<KeyboardCommand>,
        /// Records all typed text for test assertions
        pub typed_text: Arc<Mutex<Vec<String>>>,
        /// Records current typing speed
        pub current_speed: Arc<Mutex<TypingSpeed>>,
    }

    impl MockKeyboardEmulator {
        pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
            let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(10);
            let typed_text = Arc::new(Mutex::new(Vec::new()));
            let current_speed = Arc::new(Mutex::new(TypingSpeed::Normal));

            let typed_text_clone = typed_text.clone();
            let current_speed_clone = current_speed.clone();

            // Spawn a mock thread that doesn't perform actual keyboard operations
            std::thread::spawn(move || {
                while let Some(cmd) = rx.blocking_recv() {
                    match cmd {
                        KeyboardCommand::TypeText(text, cancellation_flag) => {
                            // Check if cancelled before recording
                            if !cancellation_flag.load(Ordering::Relaxed) {
                                // Just record the text, don't actually type it
                                typed_text_clone.lock().unwrap().push(text);
                            }
                        }
                        KeyboardCommand::SetSpeed(speed) => {
                            *current_speed_clone.lock().unwrap() = speed;
                        }
                    }
                }
            });

            Ok(Self {
                tx,
                typed_text,
                current_speed,
            })
        }

        pub fn set_typing_speed(&self, speed: TypingSpeed) {
            // Use try_send instead of blocking_send to avoid blocking in async context
            let _ = self.tx.try_send(KeyboardCommand::SetSpeed(speed));
        }

        pub async fn type_text(&self, text: &str, cancellation_flag: Arc<AtomicBool>) -> Result<(), Box<dyn std::error::Error>> {
            self.tx
                .send(KeyboardCommand::TypeText(text.to_string(), cancellation_flag))
                .await?;
            Ok(())
        }

        /// Get all typed text for test assertions
        pub fn get_typed_text(&self) -> Vec<String> {
            self.typed_text.lock().unwrap().clone()
        }

        /// Get current speed for test assertions
        pub fn get_current_speed(&self) -> TypingSpeed {
            *self.current_speed.lock().unwrap()
        }

        /// Clear recorded text
        pub fn clear_typed_text(&self) {
            self.typed_text.lock().unwrap().clear();
        }
    }
}
