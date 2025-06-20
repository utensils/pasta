use crate::keyboard::{KeyboardEmulator, TypingSpeed};
use std::sync::Arc;

/// Trait for clipboard operations to allow mocking in tests
pub trait ClipboardProvider: Send + Sync {
    fn get_content(&self) -> Result<Option<String>, String>;
}

/// Trait for event emission to allow mocking in tests
pub trait EventEmitter: Send + Sync {
    fn emit(&self, event: &str) -> Result<(), Box<dyn std::error::Error>>;
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
) -> Result<(), String> {
    log::info!("Paste clipboard logic triggered");

    // Get current clipboard content
    let clipboard_result = clipboard.get_content();

    match clipboard_result {
        Ok(Some(text)) => {
            log::info!("Got clipboard content, typing text");
            if let Err(e) = keyboard_emulator.type_text(&text).await {
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
    CheckItem { id: String, label: String, checked: bool },
    Submenu { label: String, items: Vec<MenuItem> },
    Separator,
}

/// Create the menu structure based on configuration
/// This is pure logic that can be tested without Tauri
pub fn create_menu_structure(typing_speed: TypingSpeed, left_click_paste: bool) -> MenuStructure {
    MenuStructure {
        items: vec![
            MenuItem::Action {
                id: "paste".to_string(),
                label: "Paste".to_string(),
            },
            MenuItem::Separator,
            MenuItem::Submenu {
                label: "Typing Speed".to_string(),
                items: vec![
                    MenuItem::CheckItem {
                        id: "speed_slow".to_string(),
                        label: "Slow".to_string(),
                        checked: typing_speed == TypingSpeed::Slow,
                    },
                    MenuItem::CheckItem {
                        id: "speed_normal".to_string(),
                        label: "Normal".to_string(),
                        checked: typing_speed == TypingSpeed::Normal,
                    },
                    MenuItem::CheckItem {
                        id: "speed_fast".to_string(),
                        label: "Fast".to_string(),
                        checked: typing_speed == TypingSpeed::Fast,
                    },
                ],
            },
            MenuItem::CheckItem {
                id: "left_click_paste".to_string(),
                label: "Left Click Pastes".to_string(),
                checked: left_click_paste,
            },
            MenuItem::Separator,
            MenuItem::Action {
                id: "quit".to_string(),
                label: "Quit".to_string(),
            },
        ],
    }
}

/// Handle menu event logic - returns what action should be taken
#[derive(Debug, PartialEq)]
pub enum MenuAction {
    Paste,
    SetTypingSpeed(TypingSpeed),
    ToggleLeftClickPaste,
    Quit,
    None,
}

/// Process menu event and return the action to take
pub fn handle_menu_event(event_id: &str) -> MenuAction {
    match event_id {
        "paste" => MenuAction::Paste,
        "speed_slow" => MenuAction::SetTypingSpeed(TypingSpeed::Slow),
        "speed_normal" => MenuAction::SetTypingSpeed(TypingSpeed::Normal),
        "speed_fast" => MenuAction::SetTypingSpeed(TypingSpeed::Fast),
        "left_click_paste" => MenuAction::ToggleLeftClickPaste,
        "quit" => MenuAction::Quit,
        _ => MenuAction::None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    // Mock implementation for testing
    struct MockClipboard {
        content: Mutex<Option<String>>,
    }

    impl MockClipboard {
        fn new(content: Option<String>) -> Self {
            Self {
                content: Mutex::new(content),
            }
        }
    }

    impl ClipboardProvider for MockClipboard {
        fn get_content(&self) -> Result<Option<String>, String> {
            Ok(self.content.lock().unwrap().clone())
        }
    }

    #[tokio::test]
    async fn test_handle_paste_clipboard_with_content() {
        let clipboard = MockClipboard::new(Some("Hello, World!".to_string()));
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_handle_paste_clipboard_empty() {
        let clipboard = MockClipboard::new(None);
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_handle_paste_clipboard_error() {
        struct ErrorClipboard;
        
        impl ClipboardProvider for ErrorClipboard {
            fn get_content(&self) -> Result<Option<String>, String> {
                Err("Clipboard access denied".to_string())
            }
        }
        
        let clipboard = ErrorClipboard;
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Clipboard access denied");
    }

    #[test]
    fn test_create_menu_structure_slow_speed() {
        let menu = create_menu_structure(TypingSpeed::Slow, false);
        
        // Verify structure
        assert_eq!(menu.items.len(), 6); // paste, separator, submenu, left_click, separator, quit
        
        // Check typing speed submenu
        if let MenuItem::Submenu { label, items } = &menu.items[2] {
            assert_eq!(label, "Typing Speed");
            assert_eq!(items.len(), 3);
            
            // Verify slow is checked
            if let MenuItem::CheckItem { label, checked, .. } = &items[0] {
                assert_eq!(label, "Slow");
                assert!(checked);
            }
        } else {
            panic!("Expected submenu at index 2");
        }
    }

    #[test]
    fn test_create_menu_structure_left_click_enabled() {
        let menu = create_menu_structure(TypingSpeed::Normal, true);
        
        // Check left click paste item
        if let MenuItem::CheckItem { label, checked, .. } = &menu.items[3] {
            assert_eq!(label, "Left Click Pastes");
            assert!(checked);
        } else {
            panic!("Expected check item at index 3");
        }
    }

    #[test]
    fn test_handle_menu_event_paste() {
        assert_eq!(handle_menu_event("paste"), MenuAction::Paste);
    }

    #[test]
    fn test_handle_menu_event_typing_speeds() {
        assert_eq!(handle_menu_event("speed_slow"), MenuAction::SetTypingSpeed(TypingSpeed::Slow));
        assert_eq!(handle_menu_event("speed_normal"), MenuAction::SetTypingSpeed(TypingSpeed::Normal));
        assert_eq!(handle_menu_event("speed_fast"), MenuAction::SetTypingSpeed(TypingSpeed::Fast));
    }

    #[test]
    fn test_handle_menu_event_left_click() {
        assert_eq!(handle_menu_event("left_click_paste"), MenuAction::ToggleLeftClickPaste);
    }

    #[test]
    fn test_handle_menu_event_quit() {
        assert_eq!(handle_menu_event("quit"), MenuAction::Quit);
    }

    #[test]
    fn test_handle_menu_event_unknown() {
        assert_eq!(handle_menu_event("unknown"), MenuAction::None);
    }

    #[test]
    fn test_menu_structure_all_items_present() {
        let menu = create_menu_structure(TypingSpeed::Fast, false);
        
        let mut found_paste = false;
        let mut found_speed_submenu = false;
        let mut found_left_click = false;
        let mut found_quit = false;
        let mut separator_count = 0;
        
        for item in &menu.items {
            match item {
                MenuItem::Action { id, .. } => {
                    if id == "paste" { found_paste = true; }
                    if id == "quit" { found_quit = true; }
                },
                MenuItem::Submenu { label, .. } => {
                    if label == "Typing Speed" { found_speed_submenu = true; }
                },
                MenuItem::CheckItem { id, .. } => {
                    if id == "left_click_paste" { found_left_click = true; }
                },
                MenuItem::Separator => { separator_count += 1; },
            }
        }
        
        assert!(found_paste);
        assert!(found_speed_submenu);
        assert!(found_left_click);
        assert!(found_quit);
        assert_eq!(separator_count, 2);
    }

    #[test]
    fn test_mock_clipboard_error() {
        struct ErrorClipboard;
        
        impl ClipboardProvider for ErrorClipboard {
            fn get_content(&self) -> Result<Option<String>, String> {
                Err("Clipboard access denied".to_string())
            }
        }
        
        let clipboard = ErrorClipboard;
        let result = clipboard.get_content();
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Clipboard access denied");
    }

    #[test]
    fn test_system_clipboard_struct() {
        // Test that SystemClipboard can be created
        let _clipboard = SystemClipboard;
        // The actual clipboard access is tested in clipboard.rs
    }

    #[test]
    fn test_menu_structure_equality() {
        let menu1 = create_menu_structure(TypingSpeed::Normal, true);
        let menu2 = create_menu_structure(TypingSpeed::Normal, true);
        
        // Both should have the same structure
        assert_eq!(menu1.items.len(), menu2.items.len());
    }

    #[test]
    fn test_menu_action_debug() {
        // Test Debug trait implementation
        assert_eq!(format!("{:?}", MenuAction::Paste), "Paste");
        assert_eq!(format!("{:?}", MenuAction::SetTypingSpeed(TypingSpeed::Slow)), "SetTypingSpeed(Slow)");
        assert_eq!(format!("{:?}", MenuAction::ToggleLeftClickPaste), "ToggleLeftClickPaste");
        assert_eq!(format!("{:?}", MenuAction::Quit), "Quit");
        assert_eq!(format!("{:?}", MenuAction::None), "None");
    }

    #[test]
    fn test_menu_item_debug() {
        // Test Debug trait implementation for MenuItem
        let action = MenuItem::Action { id: "test".to_string(), label: "Test".to_string() };
        let debug_str = format!("{:?}", action);
        assert!(debug_str.contains("Action"));
        assert!(debug_str.contains("test"));
        assert!(debug_str.contains("Test"));
    }

    #[test]
    fn test_menu_structure_debug() {
        let menu = MenuStructure { items: vec![] };
        let debug_str = format!("{:?}", menu);
        assert!(debug_str.contains("MenuStructure"));
        assert!(debug_str.contains("items"));
    }

    #[test]
    fn test_create_menu_structure_all_typing_speeds() {
        // Test menu structure for all typing speeds
        for speed in &[TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast] {
            let menu = create_menu_structure(*speed, false);
            
            // Find the typing speed submenu
            let submenu = menu.items.iter().find_map(|item| {
                if let MenuItem::Submenu { items, .. } = item {
                    Some(items)
                } else {
                    None
                }
            }).unwrap();
            
            // Count checked items - should be exactly 1
            let checked_count = submenu.iter().filter(|item| {
                if let MenuItem::CheckItem { checked, .. } = item {
                    *checked
                } else {
                    false
                }
            }).count();
            
            assert_eq!(checked_count, 1, "Exactly one typing speed should be checked");
        }
    }

    #[tokio::test]
    async fn test_handle_paste_clipboard_with_very_long_text() {
        let long_text = "x".repeat(100000); // 100k characters
        let clipboard = MockClipboard::new(Some(long_text.clone()));
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        
        let result = handle_paste_clipboard(&clipboard, &keyboard_emulator).await;
        assert!(result.is_ok());
    }
}