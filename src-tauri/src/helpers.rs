/// Helper functions extracted for better testability
use std::time::Duration;

use log::info;

/// Format log message for paste event
pub fn format_paste_event_log() -> &'static str {
    "Paste clipboard event received"
}

/// Format error message for paste failure
pub fn format_paste_error(error: &str) -> String {
    format!("Failed to handle paste: {error}")
}

/// Calculate startup delay duration
pub fn get_startup_delay() -> Duration {
    Duration::from_millis(100)
}

/// Get activation policy name for macOS
#[cfg(target_os = "macos")]
#[allow(dead_code)]
pub fn get_activation_policy() -> &'static str {
    "Accessory"
}

/// Log initialization message
pub fn log_initialization() {
    info!("Starting Pasta");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_paste_event_log() {
        let msg = format_paste_event_log();
        assert_eq!(msg, "Paste clipboard event received");
    }

    #[test]
    fn test_format_paste_error() {
        let error = format_paste_error("Clipboard access denied");
        assert_eq!(error, "Failed to handle paste: Clipboard access denied");

        let error2 = format_paste_error("Empty clipboard");
        assert_eq!(error2, "Failed to handle paste: Empty clipboard");
    }

    #[test]
    fn test_get_startup_delay() {
        let delay = get_startup_delay();
        assert_eq!(delay.as_millis(), 100);
    }

    #[test]
    #[cfg(target_os = "macos")]
    fn test_get_activation_policy() {
        let policy = get_activation_policy();
        assert_eq!(policy, "Accessory");
    }

    #[test]
    fn test_log_initialization() {
        // This just ensures the function compiles and doesn't panic
        log_initialization();
    }
}
