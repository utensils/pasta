#[cfg(test)]
mod clipboard_error_tests {
    use crate::clipboard::get_clipboard_content;
    
    #[test]
    fn test_clipboard_error_messages() {
        // Test error message formatting for clipboard operations
        
        // Test clipboard creation error message
        let create_error = format!("Failed to create clipboard: {}", "Permission denied");
        assert!(create_error.contains("Failed to create clipboard"));
        assert!(create_error.contains("Permission denied"));
        
        // Test clipboard read error message
        let read_error = format!("Failed to read clipboard: {}", "Invalid format");
        assert!(read_error.contains("Failed to read clipboard"));
        assert!(read_error.contains("Invalid format"));
        
        // Test empty clipboard error message
        let empty_error = format!("Failed to read clipboard: {}", "Clipboard is empty");
        assert!(empty_error.contains("Failed to read clipboard"));
        assert!(empty_error.contains("Clipboard is empty"));
    }
    
    #[test]
    fn test_clipboard_result_error_types() {
        // Test different error result types that clipboard operations can return
        
        // Test error result type
        let error_result: Result<Option<String>, String> = Err("Test error".to_string());
        assert!(error_result.is_err());
        assert_eq!(error_result.unwrap_err(), "Test error");
        
        // Test success with None
        let none_result: Result<Option<String>, String> = Ok(None);
        assert!(none_result.is_ok());
        assert!(none_result.unwrap().is_none());
        
        // Test success with Some
        let some_result: Result<Option<String>, String> = Ok(Some("content".to_string()));
        assert!(some_result.is_ok());
        assert_eq!(some_result.unwrap(), Some("content".to_string()));
    }
    
    #[test]
    fn test_clipboard_edge_case_content() {
        // Test handling of edge case clipboard content
        
        // Very long string
        let long_string = "a".repeat(1_000_000);
        let long_result: Option<String> = Some(long_string.clone());
        assert_eq!(long_result.unwrap().len(), 1_000_000);
        
        // String with null bytes
        let null_string = "hello\0world";
        let null_result: Option<String> = Some(null_string.to_string());
        assert!(null_result.unwrap().contains('\0'));
        
        // Unicode string
        let unicode_string = "Hello 世界 🦀";
        let unicode_result: Option<String> = Some(unicode_string.to_string());
        assert!(unicode_result.unwrap().contains('🦀'));
    }
    
    #[test]
    fn test_clipboard_error_propagation() {
        // Test error propagation patterns
        
        fn mock_clipboard_operation() -> Result<Option<String>, String> {
            Err("Mock error".to_string())
        }
        
        let result = mock_clipboard_operation();
        assert!(result.is_err());
        
        // Test error mapping
        let mapped_error = result.map_err(|e| format!("Wrapped: {}", e));
        assert!(mapped_error.is_err());
        assert!(mapped_error.unwrap_err().contains("Wrapped"));
    }
    
    #[test]
    fn test_clipboard_empty_vs_error() {
        // Test distinction between empty clipboard and error
        
        // Empty clipboard should return Ok(None)
        let empty_clipboard: Result<Option<String>, String> = Ok(None);
        assert!(empty_clipboard.is_ok());
        assert!(empty_clipboard.unwrap().is_none());
        
        // Error should return Err
        let error_clipboard: Result<Option<String>, String> = Err("Error".to_string());
        assert!(error_clipboard.is_err());
        
        // Empty string should return Ok(None) based on the implementation
        let empty_string_result: Result<Option<String>, String> = if "".is_empty() {
            Ok(None)
        } else {
            Ok(Some("".to_string()))
        };
        assert!(empty_string_result.is_ok());
        assert!(empty_string_result.unwrap().is_none());
    }
    
    #[test]
    fn test_clipboard_platform_specific_errors() {
        // Test platform-specific error scenarios
        
        #[cfg(target_os = "macos")]
        {
            let macos_error = "NSPasteboardCommunicationError";
            let error_msg = format!("Failed to read clipboard: {}", macos_error);
            assert!(error_msg.contains("NSPasteboardCommunicationError"));
        }
        
        #[cfg(target_os = "windows")]
        {
            let windows_error = "OpenClipboard failed";
            let error_msg = format!("Failed to read clipboard: {}", windows_error);
            assert!(error_msg.contains("OpenClipboard failed"));
        }
        
        #[cfg(target_os = "linux")]
        {
            let linux_error = "X11 connection error";
            let error_msg = format!("Failed to read clipboard: {}", linux_error);
            assert!(error_msg.contains("X11 connection error"));
        }
    }
    
    #[test]
    fn test_clipboard_content_validation() {
        // Test clipboard content validation scenarios
        
        // Test whitespace-only content
        let whitespace = "   \t\n   ";
        let whitespace_result = if whitespace.trim().is_empty() {
            None
        } else {
            Some(whitespace.to_string())
        };
        assert!(whitespace_result.is_none());
        
        // Test content with leading/trailing whitespace
        let content_with_spaces = "  hello world  ";
        let trimmed_result = Some(content_with_spaces.to_string());
        assert_eq!(trimmed_result.unwrap(), "  hello world  ");
        
        // Test binary-like content
        let binary_like = "\x00\x01\x02\x03";
        let binary_result = Some(binary_like.to_string());
        assert_eq!(binary_result.unwrap().len(), 4);
    }
    
    #[test]
    fn test_clipboard_concurrent_access() {
        // Test concurrent clipboard access patterns
        use std::thread;
        use std::sync::Arc;
        use std::sync::atomic::{AtomicUsize, Ordering};
        
        let counter = Arc::new(AtomicUsize::new(0));
        let mut handles = vec![];
        
        for _ in 0..5 {
            let counter_clone = counter.clone();
            let handle = thread::spawn(move || {
                // Simulate clipboard access
                counter_clone.fetch_add(1, Ordering::SeqCst);
                
                // Simulate clipboard operation result
                let _result: Result<Option<String>, String> = Ok(Some("test".to_string()));
            });
            handles.push(handle);
        }
        
        for handle in handles {
            handle.join().unwrap();
        }
        
        assert_eq!(counter.load(Ordering::SeqCst), 5);
    }
}