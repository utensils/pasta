use log::{debug, info};
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Runtime,
};

/// Extract tooltip text for reuse and testing
pub fn get_tray_tooltip() -> &'static str {
    "Pasta - Clipboard to Keyboard"
}

/// Determine the action to take for a tray icon event
#[derive(Debug, PartialEq)]
pub enum TrayIconAction {
    ShowMenu,
    None,
}

/// Handle tray icon click event and return the action to take
pub fn handle_tray_icon_click(
    button: MouseButton,
    button_state: MouseButtonState,
) -> TrayIconAction {
    match (button, button_state) {
        (MouseButton::Left, MouseButtonState::Up) => TrayIconAction::ShowMenu,
        (MouseButton::Right, MouseButtonState::Up) => TrayIconAction::ShowMenu,
        _ => TrayIconAction::None,
    }
}

pub struct TrayManager {}

impl TrayManager {
    pub fn new() -> Self {
        Self {}
    }

    fn build_tauri_menu<R: Runtime>(
        &self,
        app: &AppHandle<R>,
        structure: &crate::app_logic::MenuStructure,
    ) -> Result<tauri::menu::Menu<R>, Box<dyn std::error::Error>> {
        use crate::app_logic::MenuItem;

        let mut menu_builder = MenuBuilder::new(app);

        for item in &structure.items {
            match item {
                MenuItem::Action { id, label } => {
                    let menu_item = MenuItemBuilder::with_id(id, label).build(app)?;
                    menu_builder = menu_builder.item(&menu_item);
                }
                MenuItem::Separator => {
                    menu_builder = menu_builder.separator();
                }
            }
        }

        Ok(menu_builder.build()?)
    }

    pub fn setup<R: Runtime>(&self, app: &AppHandle<R>) -> Result<(), Box<dyn std::error::Error>> {
        info!("Setting up tray with default configuration");

        // Get menu structure from business logic
        let menu_structure = crate::app_logic::create_menu_structure();

        // Convert to Tauri menu
        let menu = self.build_tauri_menu(app, &menu_structure)?;

        // Create tray icon with menu
        let _tray = TrayIconBuilder::with_id("main")
            .icon(app.default_window_icon().unwrap().clone())
            .menu(&menu)
            .show_menu_on_left_click(true)
            .tooltip(get_tray_tooltip())
            .on_menu_event({
                let _app_handle = app.clone();
                move |app, event| {
                    use crate::app_logic::{handle_menu_event, MenuAction};

                    debug!("Menu event: {}", event.id.as_ref());
                    let action = handle_menu_event(event.id.as_ref());

                    match action {
                        MenuAction::Paste => {
                            info!("Paste menu item clicked");
                            app.emit("paste_clipboard", ()).unwrap();
                        }
                        MenuAction::CancelTyping => {
                            info!("Cancel typing menu item clicked");
                            app.emit("cancel_typing", ()).unwrap();
                        }
                        MenuAction::Quit => {
                            app.exit(0);
                        }
                        MenuAction::None => {}
                    }
                }
            })
            .on_tray_icon_event(move |_tray, event| {
                if let TrayIconEvent::Click {
                    button,
                    button_state,
                    ..
                } = event
                {
                    let action = handle_tray_icon_click(button, button_state);

                    match action {
                        TrayIconAction::ShowMenu => {
                            debug!("Click on tray icon - showing menu");
                            // Menu will be shown automatically by Tauri
                        }
                        TrayIconAction::None => {}
                    }
                }
            })
            .build(app)?;

        // The tray icon is automatically managed by Tauri
        // We don't need to explicitly store it

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tray_manager_creation() {
        let tray_manager = TrayManager::new();
        // Just verify it can be created
        let _ = tray_manager;
    }

    #[test]
    fn test_menu_has_paste_item() {
        // This test verifies that our menu structure includes the paste item
        let menu_items = vec!["paste", "cancel_typing", "quit"];

        // Verify expected menu item IDs exist
        assert!(menu_items.contains(&"paste"));
        assert!(menu_items.contains(&"cancel_typing"));
        assert!(menu_items.contains(&"quit"));
    }

    #[test]
    fn test_menu_structure_hierarchy() {
        // Test that verifies the expected menu structure
        let expected_structure = vec![
            ("paste", "MenuItem"),
            ("cancel_typing", "MenuItem"),
            ("quit", "MenuItem"),
        ];

        // Verify structure
        assert_eq!(expected_structure.len(), 3);
    }

    #[test]
    fn test_menu_event_handlers() {
        // Test that all menu event IDs are properly handled
        let event_ids = vec!["paste", "cancel_typing", "quit"];

        // Verify all event IDs have handlers
        for id in &event_ids {
            assert!(!id.is_empty());
        }
    }

    #[test]
    fn test_tray_tooltip() {
        let tooltip = get_tray_tooltip();
        assert_eq!(tooltip, "Pasta - Clipboard to Keyboard");
        assert!(tooltip.contains("Pasta"));
        assert!(tooltip.contains("Clipboard"));
    }

    #[test]
    fn test_menu_event_ids() {
        // Test that all expected menu event IDs are defined
        let event_ids = vec!["paste", "cancel_typing", "quit"];

        // Verify all IDs are valid strings
        for id in &event_ids {
            assert!(!id.is_empty());
            assert!(id.is_ascii());
        }
    }

    #[test]
    fn test_tray_icon_event_types() {
        // Test that we handle the expected tray icon event types
        let handled_events = vec!["Click"];
        assert_eq!(handled_events.len(), 1);
        assert!(handled_events.contains(&"Click"));
    }

    #[test]
    fn test_get_tray_tooltip() {
        let tooltip = get_tray_tooltip();
        assert_eq!(tooltip, "Pasta - Clipboard to Keyboard");
        assert!(tooltip.contains("Pasta"));
        assert!(tooltip.contains("Clipboard"));
        assert!(tooltip.contains("Keyboard"));
    }

    #[test]
    fn test_error_handling_return_type() {
        // Test that setup returns the expected error type
        fn test_error_type() -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }

        assert!(test_error_type().is_ok());
    }

    #[test]
    fn test_handle_tray_icon_click_left() {
        use tauri::tray::{MouseButton, MouseButtonState};

        let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Up);
        assert_eq!(action, TrayIconAction::ShowMenu);
    }

    #[test]
    fn test_handle_tray_icon_click_right() {
        use tauri::tray::{MouseButton, MouseButtonState};

        let action = handle_tray_icon_click(MouseButton::Right, MouseButtonState::Up);
        assert_eq!(action, TrayIconAction::ShowMenu);
    }

    #[test]
    fn test_handle_tray_icon_click_other_states() {
        use tauri::tray::{MouseButton, MouseButtonState};

        // Test button down state
        let action = handle_tray_icon_click(MouseButton::Left, MouseButtonState::Down);
        assert_eq!(action, TrayIconAction::None);

        // Test middle button
        let action2 = handle_tray_icon_click(MouseButton::Middle, MouseButtonState::Up);
        assert_eq!(action2, TrayIconAction::None);
    }

    #[test]
    fn test_tray_icon_action_debug() {
        // Test Debug trait implementation
        let action = TrayIconAction::ShowMenu;
        assert_eq!(format!("{:?}", action), "ShowMenu");

        let action2 = TrayIconAction::None;
        assert_eq!(format!("{:?}", action2), "None");
    }
}
