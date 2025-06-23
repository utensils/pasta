use std::sync::{atomic::AtomicBool, Arc};

use crate::keyboard::KeyboardEmulator;

/// Trait for clipboard operations to allow mocking in tests
pub trait ClipboardProvider: Send + Sync {
    fn get_content(&self) -> Result<Option<String>, String>;
}

/// Real implementation of ClipboardProvider using arboard
pub struct SystemClipboard;

impl ClipboardProvider for SystemClipboard {
    fn get_content(&self) -> Result<Option<String>, String> {
        crate::clipboard::get_clipboard_content()
    }
}

/// Business logic for paste clipboard operation
/// This is extracted from the Tauri command to be testable
pub async fn handle_paste_clipboard(
    clipboard: &dyn ClipboardProvider,
    keyboard_emulator: &Arc<KeyboardEmulator>,
    cancellation_flag: Arc<AtomicBool>,
) -> Result<(), String> {
    log::info!("Paste clipboard logic triggered");

    // Get current clipboard content
    let clipboard_result = clipboard.get_content();

    match clipboard_result {
        Ok(Some(text)) => {
            log::info!("Got clipboard content, typing text");
            if let Err(e) = keyboard_emulator.type_text(&text, cancellation_flag).await {
                log::error!("Failed to type text: {e:?}");
                return Err(format!("Failed to type text: {e}"));
            }
            Ok(())
        }
        Ok(None) => {
            log::info!("Clipboard is empty");
            Ok(())
        }
        Err(e) => {
            log::error!("Failed to get clipboard content: {e}");
            Err(e)
        }
    }
}

/// Menu structure data that can be tested independently of Tauri
#[derive(Debug, Clone, PartialEq)]
pub struct MenuStructure {
    pub items: Vec<MenuItem>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum MenuItem {
    Action { id: String, label: String },
    Separator,
}

/// Create the menu structure
/// This is pure logic that can be tested without Tauri
pub fn create_menu_structure() -> MenuStructure {
    MenuStructure {
        items: vec![
            MenuItem::Action {
                id: "paste".to_string(),
                label: "Paste".to_string(),
            },
            MenuItem::Action {
                id: "cancel_typing".to_string(),
                label: "Cancel Typing".to_string(),
            },
            MenuItem::Separator,
            MenuItem::Action {
                id: "quit".to_string(),
                label: "Quit".to_string(),
            },
        ],
    }
}

/// Menu action enum
#[derive(Debug, PartialEq)]
pub enum MenuAction {
    Paste,
    CancelTyping,
    Quit,
    None,
}

/// Handle menu event and return the action to take
pub fn handle_menu_event(event_id: &str) -> MenuAction {
    match event_id {
        "paste" => MenuAction::Paste,
        "cancel_typing" => MenuAction::CancelTyping,
        "quit" => MenuAction::Quit,
        _ => MenuAction::None,
    }
}

#[cfg(test)]
mod tests {
    use std::sync::Mutex;

    use super::*;

    /// Mock clipboard for testing
    struct MockClipboard {
        content: Arc<Mutex<Result<Option<String>, String>>>,
    }

    impl MockClipboard {
        fn new_with_content(content: &str) -> Self {
            Self {
                content: Arc::new(Mutex::new(Ok(Some(content.to_string())))),
            }
        }

        fn new_empty() -> Self {
            Self {
                content: Arc::new(Mutex::new(Ok(None))),
            }
        }

        fn new_with_error(error: &str) -> Self {
            Self {
                content: Arc::new(Mutex::new(Err(error.to_string()))),
            }
        }
    }

    impl ClipboardProvider for MockClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            self.content.lock().unwrap().clone()
        }
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_handle_paste_clipboard_with_content() {
        let clipboard = MockClipboard::new_with_content("Hello, World!");
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_handle_paste_clipboard_empty() {
        let clipboard = MockClipboard::new_empty();
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_handle_paste_clipboard_error() {
        let clipboard = MockClipboard::new_with_error("Clipboard access failed");
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Clipboard access failed");
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_handle_paste_clipboard_with_cancellation() {
        let clipboard = MockClipboard::new_with_content("Test");
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(true)); // Pre-cancelled

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_ok()); // Should complete but text might be cut short
    }

    #[tokio::test]
    #[ignore = "Requires display connection for keyboard emulator"]
    #[cfg(not(tarpaulin))]
    async fn test_handle_paste_clipboard_with_very_long_text() {
        let long_text = "a".repeat(10000);
        let clipboard = MockClipboard::new_with_content(&long_text);
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        let result =
            handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await;
        assert!(result.is_ok());
    }

    #[test]
    fn test_create_menu_structure() {
        let menu = create_menu_structure();

        // Check structure
        assert_eq!(menu.items.len(), 4); // paste, cancel_typing, separator, quit

        // Check paste item
        if let MenuItem::Action { id, label } = &menu.items[0] {
            assert_eq!(id, "paste");
            assert_eq!(label, "Paste");
        } else {
            panic!("First item should be paste action");
        }

        // Check cancel typing item
        if let MenuItem::Action { id, label } = &menu.items[1] {
            assert_eq!(id, "cancel_typing");
            assert_eq!(label, "Cancel Typing");
        } else {
            panic!("Second item should be cancel_typing action");
        }

        // Check separator
        assert!(matches!(menu.items[2], MenuItem::Separator));

        // Check quit item
        if let MenuItem::Action { id, label } = &menu.items[3] {
            assert_eq!(id, "quit");
            assert_eq!(label, "Quit");
        } else {
            panic!("Last item should be quit action");
        }
    }

    #[test]
    fn test_handle_menu_event_paste() {
        assert_eq!(handle_menu_event("paste"), MenuAction::Paste);
    }

    #[test]
    fn test_handle_menu_event_cancel_typing() {
        assert_eq!(handle_menu_event("cancel_typing"), MenuAction::CancelTyping);
    }

    #[test]
    fn test_handle_menu_event_quit() {
        assert_eq!(handle_menu_event("quit"), MenuAction::Quit);
    }

    #[test]
    fn test_handle_menu_event_unknown() {
        assert_eq!(handle_menu_event("unknown"), MenuAction::None);
        assert_eq!(handle_menu_event(""), MenuAction::None);
    }

    #[test]
    fn test_menu_structure_all_items_present() {
        let menu = create_menu_structure();

        let mut has_paste = false;
        let mut has_cancel = false;
        let mut has_quit = false;
        let mut has_separator = false;

        for item in &menu.items {
            match item {
                MenuItem::Action { id, .. } => match id.as_str() {
                    "paste" => has_paste = true,
                    "cancel_typing" => has_cancel = true,
                    "quit" => has_quit = true,
                    _ => {}
                },
                MenuItem::Separator => has_separator = true,
            }
        }

        assert!(has_paste, "Menu should have paste item");
        assert!(has_cancel, "Menu should have cancel typing item");
        assert!(has_quit, "Menu should have quit item");
        assert!(has_separator, "Menu should have separator");
    }

    #[test]
    fn test_menu_structure_has_cancel_typing() {
        let menu = create_menu_structure();

        let cancel_item = menu.items.iter().find(|item| {
            if let MenuItem::Action { id, .. } = item {
                id == "cancel_typing"
            } else {
                false
            }
        });

        assert!(cancel_item.is_some());
        if let Some(MenuItem::Action { label, .. }) = cancel_item {
            assert!(label.contains("Cancel Typing"));
        }
    }

    #[test]
    fn test_cancel_typing_menu_position() {
        let menu = create_menu_structure();

        // Cancel typing should be after paste and before separator
        if let MenuItem::Action { id, .. } = &menu.items[1] {
            assert_eq!(id, "cancel_typing");
        } else {
            panic!("Cancel typing should be at position 1");
        }
    }

    #[test]
    fn test_system_clipboard_struct() {
        // Just verify SystemClipboard can be created
        let _clipboard = SystemClipboard;
    }

    #[test]
    fn test_mock_clipboard_error() {
        let clipboard = MockClipboard::new_with_error("Test error");
        let result = clipboard.get_content();
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Test error");
    }

    #[test]
    fn test_menu_action_debug() {
        assert_eq!(format!("{:?}", MenuAction::Paste), "Paste");
        assert_eq!(format!("{:?}", MenuAction::CancelTyping), "CancelTyping");
        assert_eq!(format!("{:?}", MenuAction::Quit), "Quit");
        assert_eq!(format!("{:?}", MenuAction::None), "None");
    }

    #[test]
    fn test_menu_item_debug() {
        let action = MenuItem::Action {
            id: "test".to_string(),
            label: "Test".to_string(),
        };
        let debug_str = format!("{:?}", action);
        assert!(debug_str.contains("Action"));
        assert!(debug_str.contains("test"));
        assert!(debug_str.contains("Test"));

        let separator = MenuItem::Separator;
        assert_eq!(format!("{:?}", separator), "Separator");
    }

    #[test]
    fn test_menu_structure_debug() {
        let menu = create_menu_structure();
        let debug_str = format!("{:?}", menu);
        assert!(debug_str.contains("MenuStructure"));
        assert!(debug_str.contains("items"));
    }

    #[test]
    fn test_menu_structure_equality() {
        let menu1 = create_menu_structure();
        let menu2 = create_menu_structure();
        assert_eq!(menu1, menu2);
    }
}
