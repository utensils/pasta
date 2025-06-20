use arboard::Clipboard;
use log::error;

/// Get the current clipboard content as text
pub fn get_clipboard_content() -> Result<Option<String>, String> {
    let mut clipboard = match Clipboard::new() {
        Ok(c) => c,
        Err(e) => return Err(format!("Failed to create clipboard: {e}")),
    };

    match clipboard.get_text() {
        Ok(text) => {
            if text.is_empty() {
                Ok(None)
            } else {
                Ok(Some(text))
            }
        }
        Err(e) => {
            error!("Failed to read clipboard: {e:?}");
            Err(format!("Failed to read clipboard: {e}"))
        }
    }
}

#[cfg(test)]
mod tests {
    use serial_test::serial;

    use super::*;

    // Note: These tests require a display server (X11/Wayland) to run
    // They are excluded from CI runs with: cargo test -- --skip clipboard::tests

    #[test]
    #[serial]
    fn test_get_clipboard_content() {
        // Set clipboard content
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "test clipboard content";
        clipboard.set_text(test_text).unwrap();

        // Get content and verify
        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text.to_string()));
    }

    #[test]
    #[serial]
    fn test_get_empty_clipboard() {
        // Clear clipboard
        let mut clipboard = Clipboard::new().unwrap();
        clipboard.set_text("").unwrap();

        // Get content and verify it returns None for empty
        let result = get_clipboard_content().unwrap();
        assert_eq!(result, None);
    }

    #[test]
    #[serial]
    fn test_clipboard_with_unicode() {
        // Test with unicode content
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "Hello 世界 🌍";
        clipboard.set_text(test_text).unwrap();

        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text.to_string()));
    }

    #[test]
    #[serial]
    fn test_clipboard_with_newlines() {
        // Test with multiline content
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "Line 1\nLine 2\nLine 3";
        clipboard.set_text(test_text).unwrap();

        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text.to_string()));
    }

    #[test]
    #[serial]
    fn test_clipboard_with_tabs() {
        // Test with tab characters
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "Column1\tColumn2\tColumn3";
        clipboard.set_text(test_text).unwrap();

        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text.to_string()));
    }

    #[test]
    #[serial]
    fn test_clipboard_with_special_chars() {
        // Test with special characters
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?";
        clipboard.set_text(test_text).unwrap();

        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text.to_string()));
    }

    #[test]
    #[serial]
    fn test_clipboard_with_long_text() {
        // Test with long text
        let mut clipboard = Clipboard::new().unwrap();
        let test_text = "a".repeat(10000); // 10k characters
        clipboard.set_text(&test_text).unwrap();

        let result = get_clipboard_content().unwrap();
        assert_eq!(result, Some(test_text));
    }

    #[test]
    fn test_error_string_formatting() {
        // Test error message formatting
        let error_msg = format!("Failed to create clipboard: {}", "test error");
        assert!(error_msg.contains("Failed to create clipboard"));
        assert!(error_msg.contains("test error"));

        let error_msg2 = format!("Failed to read clipboard: {}", "another error");
        assert!(error_msg2.contains("Failed to read clipboard"));
        assert!(error_msg2.contains("another error"));
    }
}
