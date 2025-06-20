use arboard::Clipboard;
use log::error;

/// Get the current clipboard content as text
pub fn get_clipboard_content() -> Result<Option<String>, String> {
    let mut clipboard = match Clipboard::new() {
        Ok(c) => c,
        Err(e) => return Err(format!("Failed to create clipboard: {}", e)),
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
            Err(format!("Failed to read clipboard: {}", e))
        }
    }
}

#[cfg(test)]
mod tests {
    use serial_test::serial;

    use super::*;

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
}
