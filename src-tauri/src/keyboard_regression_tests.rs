#[cfg(test)]
mod tests {
    use std::{
        sync::{atomic::AtomicBool, Arc, Mutex},
        time::Duration,
    };

    use crate::mock_keyboard::MockKeyboardEmulator;

    #[test]
    fn test_space_handling_in_commands() {
        // Test that spaces are preserved correctly in typed text
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        // The original command that failed
        let test_command = "zfs create -o mountpoint=/var/lib/n8n -o compression=off -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=16k -o logbias=throughput zroot/n8n";

        // Type the command
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard
                .type_text(test_command, cancellation_flag)
                .await
                .unwrap();
        });

        // Give the mock thread time to process
        std::thread::sleep(Duration::from_millis(50));

        // Verify the typed text matches the input
        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);
        assert_eq!(typed_texts[0], test_command);

        // Verify spaces are preserved
        assert!(typed_texts[0].contains(" "));
        assert!(!typed_texts[0].contains("a-o")); // Should not convert spaces to 'a'
    }

    #[test]
    fn test_multiple_spaces_preserved() {
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let test_text = "hello    world  test";

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard
                .type_text(test_text, cancellation_flag)
                .await
                .unwrap();
        });

        std::thread::sleep(Duration::from_millis(50));

        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);
        assert_eq!(typed_texts[0], test_text);
    }

    #[test]
    fn test_mixed_characters_with_spaces() {
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let test_text = "abc def-ghi_jkl mno";

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard
                .type_text(test_text, cancellation_flag)
                .await
                .unwrap();
        });

        std::thread::sleep(Duration::from_millis(50));

        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);
        assert_eq!(typed_texts[0], test_text);

        // Ensure no 'a' characters were inserted where spaces should be
        assert!(!typed_texts[0].contains("abcadef"));
    }

    // Integration test with actual keyboard emulator (marked as ignored)
    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_real_keyboard_space_handling() {
        use crate::keyboard::KeyboardEmulator;

        // Create a buffer to capture what would be typed
        let typed_buffer = Arc::new(Mutex::new(String::new()));
        let _buffer_clone = typed_buffer.clone();

        // Create a thread to simulate capturing keyboard output
        std::thread::spawn(move || {
            // In a real test, we would capture the actual keyboard output
            // For now, we'll just test that the keyboard emulator accepts the input
        });

        let keyboard = KeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        // Test with a simple command containing spaces
        let test_command = "echo hello world";
        keyboard
            .type_text(test_command, cancellation_flag)
            .await
            .unwrap();

        // Give time for typing to complete
        tokio::time::sleep(Duration::from_secs(1)).await;
    }

    #[test]
    fn test_space_character_explicitly() {
        // Test that space character is handled correctly
        let space_char = ' ';
        assert_eq!(space_char.to_string(), " ");
        assert_ne!(space_char.to_string(), "a");

        // Test that space is not a special character like \n or \t
        assert!(space_char != '\n');
        assert!(space_char != '\t');
    }

    #[test]
    fn test_mock_keyboard_clear_typed_text() {
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard.type_text("test", cancellation_flag).await.unwrap();
        });

        std::thread::sleep(Duration::from_millis(50));

        // Verify text was recorded
        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);

        // Clear the typed text
        keyboard.clear_typed_text();

        // Verify it was cleared
        let typed_texts_after_clear = keyboard.get_typed_text();
        assert_eq!(typed_texts_after_clear.len(), 0);
    }

    #[test]
    fn test_idrac_console_command_regression() {
        // Regression test for the specific iDrac console issue
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        // The exact command that was typed incorrectly in iDrac
        let original_command = "zfs create -o mountpoint=/var/lib/n8n -o compression=off -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=16k -o logbias=throughput zroot/n8n";

        // What was incorrectly typed before the fix (spaces and numbers replaced with 'a')
        let incorrect_output = "zfsacreatea-oamountpoint=/var/lib/nana-oacompression=offa-oaatime=offa-oaxattr=saa-oaacltype=posixacla-oarecordsize=aaka-oalogbias=throughputazroot/nan";

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard
                .type_text(original_command, cancellation_flag)
                .await
                .unwrap();
        });

        std::thread::sleep(Duration::from_millis(50));

        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);

        // Verify the command is typed correctly with spaces preserved
        assert_eq!(typed_texts[0], original_command);

        // Ensure it doesn't match the incorrect output
        assert_ne!(typed_texts[0], incorrect_output);

        // Specific checks for the space bug pattern
        assert!(!typed_texts[0].contains("a-o"));
        assert!(!typed_texts[0].contains("zfsacreate"));
        assert!(typed_texts[0].contains("zfs create"));

        // Specific checks for the number bug pattern
        assert!(typed_texts[0].contains("n8n"));
        assert!(!typed_texts[0].contains("nan"));
        assert!(typed_texts[0].contains("16k"));
        assert!(!typed_texts[0].contains("aak"));

        // Verify correct number of spaces
        let space_count = typed_texts[0].chars().filter(|&c| c == ' ').count();
        assert_eq!(space_count, 16); // The original command has 16 spaces

        // Verify numbers are preserved
        let number_count = typed_texts[0]
            .chars()
            .filter(|c| c.is_ascii_digit())
            .count();
        assert_eq!(number_count, 4); // The command has 4 digits: 8, 1, 6, 8
    }

    #[test]
    fn test_number_preservation() {
        // Test that numbers are not converted to 'a' characters
        let keyboard = MockKeyboardEmulator::new().unwrap();
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let test_text = "0123456789 test 16k n8n";

        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            keyboard
                .type_text(test_text, cancellation_flag)
                .await
                .unwrap();
        });

        std::thread::sleep(Duration::from_millis(50));

        let typed_texts = keyboard.get_typed_text();
        assert_eq!(typed_texts.len(), 1);
        assert_eq!(typed_texts[0], test_text);

        // Ensure all digits are preserved
        for digit in '0'..='9' {
            assert!(typed_texts[0].contains(digit));
        }

        // Ensure no 'a' characters replaced numbers
        let original_without_a = test_text.chars().filter(|&c| c != 'a').collect::<String>();
        let typed_without_a = typed_texts[0]
            .chars()
            .filter(|&c| c != 'a')
            .collect::<String>();
        assert_eq!(original_without_a, typed_without_a);
    }
}
