use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
    sync::{Arc, Mutex},
    time::Duration,
};

use arboard::Clipboard;
use log::{debug, error};
use tokio::{sync::mpsc, time::interval};

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
        let mut clipboard = Clipboard::new()?;

        // Initialize with current clipboard content hash to prevent automatic paste on startup
        let initial_hash = match clipboard.get_text() {
            Ok(text) => {
                let mut hasher = DefaultHasher::new();
                text.hash(&mut hasher);
                hasher.finish()
            }
            Err(_) => 0,
        };

        Ok(Self {
            clipboard: Arc::new(Mutex::new(clipboard)),
            last_hash: Arc::new(Mutex::new(initial_hash)),
            enabled: Arc::new(Mutex::new(true)),
        })
    }

    pub fn set_enabled(&self, enabled: bool) {
        *self.enabled.lock().unwrap() = enabled;

        // When enabling, update last_hash to current clipboard content to prevent immediate paste
        if enabled {
            if let Ok(text) = self.clipboard.lock().unwrap().get_text() {
                let mut hasher = DefaultHasher::new();
                text.hash(&mut hasher);
                let current_hash = hasher.finish();
                *self.last_hash.lock().unwrap() = current_hash;
                debug!("Updated last_hash on enable to prevent immediate paste");
            }
        }
    }

    pub fn is_enabled(&self) -> bool {
        *self.enabled.lock().unwrap()
    }

    #[cfg(test)]
    pub fn get_last_hash(&self) -> u64 {
        *self.last_hash.lock().unwrap()
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
                    debug!("Failed to read clipboard: {e:?}");
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
                    error!("Failed to send clipboard event: {e:?}");
                    break;
                }
            }
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use serial_test::serial;

    use super::*;

    #[test]
    #[serial]
    fn test_new_clipboard_monitor_initializes_with_current_hash() {
        // This test requires clipboard access, so it might fail in CI
        let monitor = ClipboardMonitor::new().unwrap();

        // The initial hash should not be 0 if there's content in the clipboard
        let _initial_hash = monitor.get_last_hash();

        // Set some content and verify hash changes
        let mut clipboard = Clipboard::new().unwrap();
        let _ = clipboard.set_text("test content");

        let monitor2 = ClipboardMonitor::new().unwrap();
        let new_hash = monitor2.get_last_hash();

        // If clipboard had content, the hash should be non-zero
        if clipboard.get_text().is_ok() {
            assert_ne!(new_hash, 0);
        }
    }

    #[test]
    fn test_set_enabled() {
        let monitor = ClipboardMonitor::new().unwrap();

        // Should start enabled
        assert!(monitor.is_enabled());

        // Test disabling
        monitor.set_enabled(false);
        assert!(!monitor.is_enabled());

        // Test re-enabling
        monitor.set_enabled(true);
        assert!(monitor.is_enabled());
    }

    #[test]
    #[serial]
    fn test_enable_updates_hash() {
        let monitor = ClipboardMonitor::new().unwrap();
        let _initial_hash = monitor.get_last_hash();

        // Disable monitor
        monitor.set_enabled(false);

        // Change clipboard content
        let mut clipboard = Clipboard::new().unwrap();
        let _ = clipboard.set_text("new test content for hash update");

        // Re-enable should update the hash
        monitor.set_enabled(true);
        let new_hash = monitor.get_last_hash();

        // Hash should be different if clipboard content changed
        assert_ne!(_initial_hash, new_hash);
    }
}
