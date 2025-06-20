/// Helper functions extracted for better testability
use std::time::Duration;

use log::info;

/// Format log message for initial config
pub fn format_initial_config_log(
    typing_speed: &crate::keyboard::TypingSpeed,
    left_click_paste: bool,
) -> String {
    format!(
        "Initial config loaded: typing_speed={typing_speed:?}, left_click_paste={left_click_paste}"
    )
}

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

/// Get event names used in the app
pub fn get_event_names() -> (&'static str, &'static str) {
    ("config_changed", "paste_clipboard")
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
    use crate::keyboard::TypingSpeed;

    #[test]
    fn test_format_initial_config_log() {
        let msg = format_initial_config_log(&TypingSpeed::Normal, false);
        assert!(msg.contains("Initial config loaded"));
        assert!(msg.contains("typing_speed=Normal"));
        assert!(msg.contains("left_click_paste=false"));

        let msg2 = format_initial_config_log(&TypingSpeed::Fast, true);
        assert!(msg2.contains("typing_speed=Fast"));
        assert!(msg2.contains("left_click_paste=true"));
    }

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
    fn test_get_event_names() {
        let (config_event, paste_event) = get_event_names();
        assert_eq!(config_event, "config_changed");
        assert_eq!(paste_event, "paste_clipboard");
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
