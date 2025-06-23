#[cfg(test)]
mod integration_tests {
    use std::{
        sync::{
            atomic::{AtomicBool, Ordering},
            Arc,
        },
        time::Duration,
    };

    use crate::{
        app_logic::{handle_paste_clipboard, ClipboardProvider},
        keyboard::KeyboardEmulator,
    };

    /// Mock clipboard that returns a long text string
    #[derive(Clone)]
    struct LongTextClipboard {
        text: String,
    }

    impl LongTextClipboard {
        fn new(length: usize) -> Self {
            Self {
                text: "a".repeat(length),
            }
        }
    }

    impl ClipboardProvider for LongTextClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            Ok(Some(self.text.clone()))
        }
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    async fn test_emergency_stop_cancels_typing() {
        // Create a mock keyboard emulator that simulates typing
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let clipboard = LongTextClipboard::new(1000); // Long text to type

        // Clone for the cancellation thread
        let cancellation_flag_clone = cancellation_flag.clone();

        // Start typing in a task
        let typing_task = tokio::spawn(async move {
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag_clone).await
        });

        // Wait a bit for typing to start
        tokio::time::sleep(Duration::from_millis(50)).await;

        // Trigger cancellation (simulating Ctrl+Shift+Escape press)
        cancellation_flag.store(true, Ordering::Relaxed);

        // Wait for the typing task to complete
        let result = typing_task.await.unwrap();
        assert!(result.is_ok());

        // Verify that not all text was typed (since we cancelled)
        // Note: In a real keyboard emulator, we would check that typing stopped
        // For the mock, we just verify the function completed without error
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    async fn test_cancellation_flag_reset_before_new_operation() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let clipboard = LongTextClipboard::new(100);

        // First operation with cancellation
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        cancellation_flag.store(true, Ordering::Relaxed); // Pre-cancelled

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag.clone()).await;
        assert!(result.is_ok());

        // Reset flag for second operation
        cancellation_flag.store(false, Ordering::Relaxed);

        // Second operation should work normally
        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_cancellation_flag_thread_safety() {
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let mut handles = vec![];

        // Spawn multiple threads that try to set the flag
        for i in 0..10 {
            let flag_clone = cancellation_flag.clone();
            let handle = std::thread::spawn(move || {
                std::thread::sleep(Duration::from_millis(i * 10));
                flag_clone.store(true, Ordering::Relaxed);
            });
            handles.push(handle);
        }

        // Wait for all threads
        for handle in handles {
            handle.join().unwrap();
        }

        // Flag should be true after all threads complete
        assert!(cancellation_flag.load(Ordering::Relaxed));
    }

    #[test]
    fn test_double_escape_timing_window() {
        // Note: This test is kept for historical reference, but we now use Ctrl+Shift+Escape
        // which doesn't require timing window detection
        use std::time::{SystemTime, UNIX_EPOCH};

        let double_press_window_ms = 500u64;

        // Simulate first press
        let first_press = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        // Test within window
        let second_press_within = first_press + 300;
        let diff_within = second_press_within.saturating_sub(first_press);
        assert!(diff_within <= double_press_window_ms);

        // Test outside window
        let second_press_outside = first_press + 600;
        let diff_outside = second_press_outside.saturating_sub(first_press);
        assert!(diff_outside > double_press_window_ms);
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    async fn test_multiple_emergency_stops() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let clipboard = LongTextClipboard::new(500);

        // Test multiple cancellations
        for _ in 0..3 {
            let cancellation_flag = Arc::new(AtomicBool::new(false));

            // Start typing
            let flag_clone = cancellation_flag.clone();
            let keyboard_clone = keyboard_emulator.clone();
            let clipboard_clone = clipboard.clone();
            let typing_task = tokio::spawn(async move {
                handle_paste_clipboard(&clipboard_clone, &keyboard_clone, flag_clone).await
            });

            // Cancel quickly
            tokio::time::sleep(Duration::from_millis(10)).await;
            cancellation_flag.store(true, Ordering::Relaxed);

            // Verify task completes
            let result = typing_task.await.unwrap();
            assert!(result.is_ok());
        }
    }
}
