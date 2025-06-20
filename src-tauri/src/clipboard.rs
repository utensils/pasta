use arboard::Clipboard;
use log::{debug, error};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::sync::mpsc;
use tokio::time::interval;

#[derive(Debug, Clone)]
pub enum ClipboardEvent {
    ContentChanged(String),
}

pub struct ClipboardMonitor {
    clipboard: Arc<Mutex<Clipboard>>,
    last_hash: Arc<Mutex<u64>>,
    enabled: Arc<Mutex<bool>>,
}

impl ClipboardMonitor {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let clipboard = Clipboard::new()?;
        Ok(Self {
            clipboard: Arc::new(Mutex::new(clipboard)),
            last_hash: Arc::new(Mutex::new(0)),
            enabled: Arc::new(Mutex::new(true)),
        })
    }

    pub fn set_enabled(&self, enabled: bool) {
        *self.enabled.lock().unwrap() = enabled;
    }

    pub fn is_enabled(&self) -> bool {
        *self.enabled.lock().unwrap()
    }

    pub async fn start_monitoring(
        self: Arc<Self>,
        tx: mpsc::Sender<ClipboardEvent>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let mut interval = interval(Duration::from_millis(500));

        loop {
            interval.tick().await;

            if !self.is_enabled() {
                continue;
            }

            let content = match self.clipboard.lock().unwrap().get_text() {
                Ok(text) => text,
                Err(e) => {
                    debug!("Failed to read clipboard: {:?}", e);
                    continue;
                }
            };

            let mut hasher = DefaultHasher::new();
            content.hash(&mut hasher);
            let current_hash = hasher.finish();

            let should_send = {
                let mut last_hash = self.last_hash.lock().unwrap();
                if current_hash != *last_hash && !content.is_empty() {
                    *last_hash = current_hash;
                    true
                } else {
                    false
                }
            };

            if should_send {
                debug!("Clipboard content changed");
                if let Err(e) = tx.send(ClipboardEvent::ContentChanged(content)).await {
                    error!("Failed to send clipboard event: {:?}", e);
                    break;
                }
            }
        }

        Ok(())
    }
}