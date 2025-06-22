#[cfg(test)]
pub use mock::MockKeyboardEmulator;

#[cfg(test)]
mod mock {
    use std::sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    };

    use tokio::sync::mpsc;

    use crate::keyboard::KeyboardCommand;

    /// A mock keyboard emulator that doesn't perform actual keyboard operations
    /// Used for testing to prevent tests from typing on the system
    pub struct MockKeyboardEmulator {
        tx: mpsc::Sender<KeyboardCommand>,
        /// Records all typed text for test assertions
        pub typed_text: Arc<Mutex<Vec<String>>>,
    }

    impl MockKeyboardEmulator {
        pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
            let (tx, mut rx) = mpsc::channel::<KeyboardCommand>(10);
            let typed_text = Arc::new(Mutex::new(Vec::new()));

            let typed_text_clone = typed_text.clone();

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
                    }
                }
            });

            Ok(Self { tx, typed_text })
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

        /// Get all text that has been "typed" for test assertions
        pub fn get_typed_text(&self) -> Vec<String> {
            self.typed_text.lock().unwrap().clone()
        }

        /// Clear the recorded typed text
        pub fn clear_typed_text(&self) {
            self.typed_text.lock().unwrap().clear();
        }
    }
}
