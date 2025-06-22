use std::sync::{
    atomic::{AtomicBool, AtomicU64, Ordering},
    Arc,
};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use log::{debug, info};
use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut};

/// Manages global hotkeys for the application
pub struct HotkeyManager {
    last_escape_time: Arc<AtomicU64>,
    double_press_window_ms: u64,
}

impl HotkeyManager {
    pub fn new() -> Self {
        Self {
            last_escape_time: Arc::new(AtomicU64::new(0)),
            double_press_window_ms: 500, // 500ms window for double-press
        }
    }

    /// Register the global hotkeys
    pub fn register_hotkeys<R: tauri::Runtime>(
        &self,
        app_handle: &AppHandle<R>,
        cancellation_flag: Arc<AtomicBool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let escape_shortcut = Shortcut::new(None, Code::Escape);
        let last_escape_time = self.last_escape_time.clone();
        let double_press_window = self.double_press_window_ms;

        app_handle.global_shortcut().on_shortcut(
            escape_shortcut,
            move |app_handle, _shortcut, _event| {
                let current_time = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_millis() as u64;

                let last_time = last_escape_time.load(Ordering::Relaxed);
                let time_diff = current_time.saturating_sub(last_time);

                debug!("Escape pressed. Time since last: {}ms", time_diff);

                if time_diff <= double_press_window {
                    // Double-press detected
                    info!("Double-Escape detected! Cancelling typing operation");
                    cancellation_flag.store(true, Ordering::Relaxed);
                    last_escape_time.store(0, Ordering::Relaxed); // Reset to prevent triple-press
                    
                    // Optional: Emit an event for UI feedback
                    let _ = app_handle.emit("typing_cancelled", ());
                } else {
                    // First press or too much time has passed
                    last_escape_time.store(current_time, Ordering::Relaxed);
                }
            },
        )?;

        info!("Registered double-Escape hotkey for emergency stop");
        Ok(())
    }

    /// Alternative: Register Ctrl+Shift+Escape for simpler implementation
    pub fn register_ctrl_shift_escape<R: tauri::Runtime>(
        &self,
        app_handle: &AppHandle<R>,
        cancellation_flag: Arc<AtomicBool>,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let shortcut = Shortcut::new(
            Some(Modifiers::CONTROL | Modifiers::SHIFT),
            Code::Escape,
        );

        app_handle.global_shortcut().on_shortcut(
            shortcut,
            move |app_handle, _shortcut, _event| {
                info!("Ctrl+Shift+Escape pressed! Cancelling typing operation");
                cancellation_flag.store(true, Ordering::Relaxed);
                
                // Optional: Emit an event for UI feedback
                let _ = app_handle.emit("typing_cancelled", ());
            },
        )?;

        info!("Registered Ctrl+Shift+Escape hotkey for emergency stop");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hotkey_manager_creation() {
        let manager = HotkeyManager::new();
        assert_eq!(manager.double_press_window_ms, 500);
        assert_eq!(manager.last_escape_time.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn test_time_difference_calculation() {
        let current_time = 1000u64;
        let last_time = 600u64;
        let diff = current_time.saturating_sub(last_time);
        assert_eq!(diff, 400);

        // Test saturating subtraction
        let current_time = 100u64;
        let last_time = 200u64;
        let diff = current_time.saturating_sub(last_time);
        assert_eq!(diff, 0);
    }

    #[test]
    fn test_double_press_detection_logic() {
        let double_press_window = 500u64;

        // Within window
        let time_diff = 300u64;
        assert!(time_diff <= double_press_window);

        // Exactly at window boundary
        let time_diff = 500u64;
        assert!(time_diff <= double_press_window);

        // Outside window
        let time_diff = 501u64;
        assert!(!(time_diff <= double_press_window));
    }

    #[test]
    fn test_atomic_operations() {
        let atomic_time = Arc::new(AtomicU64::new(0));
        
        // Test store and load
        atomic_time.store(1000, Ordering::Relaxed);
        assert_eq!(atomic_time.load(Ordering::Relaxed), 1000);

        // Test with clone
        let cloned = atomic_time.clone();
        cloned.store(2000, Ordering::Relaxed);
        assert_eq!(atomic_time.load(Ordering::Relaxed), 2000);
    }

    #[test]
    fn test_cancellation_flag_operations() {
        let flag = Arc::new(AtomicBool::new(false));
        
        // Test initial state
        assert!(!flag.load(Ordering::Relaxed));

        // Test setting to true
        flag.store(true, Ordering::Relaxed);
        assert!(flag.load(Ordering::Relaxed));

        // Test resetting
        flag.store(false, Ordering::Relaxed);
        assert!(!flag.load(Ordering::Relaxed));
    }

    #[test]
    fn test_system_time_conversion() {
        let time = SystemTime::now();
        let duration = time.duration_since(UNIX_EPOCH).unwrap();
        let millis = duration.as_millis() as u64;
        
        assert!(millis > 0);
        assert!(millis < u64::MAX);
    }

    #[test]
    fn test_shortcut_creation() {
        // Test escape without modifiers
        let escape_shortcut = Shortcut::new(None, Code::Escape);
        assert!(matches!(escape_shortcut.key, Code::Escape));

        // Test ctrl+shift+escape
        let ctrl_shift_escape = Shortcut::new(
            Some(Modifiers::CONTROL | Modifiers::SHIFT),
            Code::Escape,
        );
        assert!(matches!(ctrl_shift_escape.key, Code::Escape));
    }
}