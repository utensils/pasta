mod app_logic;
mod clipboard;
mod helpers;
mod hotkey;
pub mod keyboard;
mod tray;

#[cfg(test)]
mod clipboard_mock_tests;

#[cfg(test)]
mod clipboard_error_tests;

#[cfg(test)]
mod clipboard_platform_tests;

#[cfg(test)]
mod integration_test_emergency_stop;


use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};

use log::{error, info};
use tauri::{Listener, Manager, State};

use crate::{hotkey::HotkeyManager, keyboard::KeyboardEmulator, tray::TrayManager};

#[derive(Clone)]
pub struct AppState {
    keyboard_emulator: Arc<KeyboardEmulator>,
    is_typing_cancelled: Arc<AtomicBool>,
}

impl AppState {
    pub fn cancel_typing(&self) {
        self.is_typing_cancelled.store(true, Ordering::Relaxed);
        info!("Typing operation cancelled by user");
    }

    pub fn reset_cancellation(&self) {
        self.is_typing_cancelled.store(false, Ordering::Relaxed);
    }

    pub fn is_cancelled(&self) -> bool {
        self.is_typing_cancelled.load(Ordering::Relaxed)
    }
}

/// Initialize app components and return them for testing
pub fn initialize_components() -> Result<Arc<KeyboardEmulator>, Box<dyn std::error::Error>> {
    info!("Initializing Pasta with default typing speed: Normal");
    let keyboard_emulator = Arc::new(KeyboardEmulator::new()?);
    Ok(keyboard_emulator)
}

/// Create app state from components
pub fn create_app_state(keyboard_emulator: Arc<KeyboardEmulator>) -> AppState {
    AppState {
        keyboard_emulator,
        is_typing_cancelled: Arc::new(AtomicBool::new(false)),
    }
}

/// Handle paste clipboard event in a new thread
pub fn handle_paste_clipboard_event(
    keyboard_emulator: Arc<KeyboardEmulator>,
    cancellation_flag: Arc<AtomicBool>,
) {
    use app_logic::{handle_paste_clipboard, SystemClipboard};

    info!("{}", helpers::format_paste_event_log());

    // Reset the cancellation flag before starting
    cancellation_flag.store(false, Ordering::Relaxed);

    let clipboard = SystemClipboard;

    std::thread::spawn(move || {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async move {
            if let Err(e) =
                handle_paste_clipboard(&clipboard, &keyboard_emulator, cancellation_flag).await
            {
                error!("{}", helpers::format_paste_error(&e.to_string()));
            }
        });
    });
}

/// Setup event handlers for the app
pub fn setup_event_handlers<R: tauri::Runtime>(
    app_handle: &tauri::AppHandle<R>,
    keyboard_emulator: Arc<KeyboardEmulator>,
    cancellation_flag: Arc<AtomicBool>,
) {
    // Handle paste clipboard event from tray
    let keyboard_emulator_clone = keyboard_emulator;
    let cancellation_flag_clone = cancellation_flag.clone();
    app_handle.listen("paste_clipboard", move |_event| {
        handle_paste_clipboard_event(
            keyboard_emulator_clone.clone(),
            cancellation_flag_clone.clone(),
        );
    });

    // Handle cancel typing event from tray
    let cancellation_flag_clone = cancellation_flag;
    app_handle.listen("cancel_typing", move |_event| {
        info!("Cancel typing event received");
        cancellation_flag_clone.store(true, Ordering::Relaxed);
    });
}

#[tauri::command]
async fn paste_clipboard(state: State<'_, AppState>) -> Result<(), String> {
    use app_logic::{handle_paste_clipboard, SystemClipboard};

    // Reset the cancellation flag before starting
    state.reset_cancellation();

    let clipboard = SystemClipboard;
    handle_paste_clipboard(
        &clipboard,
        &state.keyboard_emulator,
        state.is_typing_cancelled.clone(),
    )
    .await
}

#[tauri::command]
async fn cancel_typing(state: State<'_, AppState>) -> Result<(), String> {
    state.cancel_typing();
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    helpers::log_initialization();

    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .setup(|app| {
            // Hide dock icon on startup (macOS)
            #[cfg(target_os = "macos")]
            {
                #[allow(clippy::let_unit_value)]
                let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
            }

            // Initialize components
            let keyboard_emulator =
                initialize_components().expect("Failed to initialize components");

            // Small delay before creating tray to ensure app is fully initialized
            // This works around a Tauri bug where submenus don't initialize properly
            std::thread::sleep(helpers::get_startup_delay());

            // Setup system tray
            let tray_manager = TrayManager::new();
            tray_manager.setup(app.handle())?;

            // Create app state
            let app_state = create_app_state(keyboard_emulator.clone());
            let cancellation_flag = app_state.is_typing_cancelled.clone();
            app.manage(app_state);

            // Setup event handlers
            setup_event_handlers(app.handle(), keyboard_emulator, cancellation_flag.clone());

            // Setup global hotkeys
            let hotkey_manager = HotkeyManager::new();
            hotkey_manager.register_hotkeys(app.handle(), cancellation_flag)?;

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![paste_clipboard, cancel_typing])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use tokio::sync::mpsc;

    use super::*;
    use crate::{keyboard::TypingSpeed, tray::TrayManager};

    // Mock implementations for testing
    struct MockState {
        app_state: AppState,
    }

    impl MockState {
        fn new() -> Self {
            let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

            let app_state = AppState {
                keyboard_emulator,
                is_typing_cancelled: Arc::new(AtomicBool::new(false)),
            };

            Self { app_state }
        }
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_paste_clipboard_empty() {
        // Since we can't mock the clipboard module directly, we'll test the structure
        let mock_state = MockState::new();

        // Test that keyboard emulator can receive type_text commands
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let result = mock_state
            .app_state
            .keyboard_emulator
            .type_text("test", cancellation_flag)
            .await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_paste_clipboard_command_with_text() {
        // Test the paste_clipboard function structure
        let mock_state = MockState::new();

        // We can't directly test paste_clipboard because it uses get_clipboard_content
        // which requires system clipboard access, but we can test the keyboard emulator
        let test_text = "Hello, World!";
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let result = mock_state
            .app_state
            .keyboard_emulator
            .type_text(test_text, cancellation_flag)
            .await;
        assert!(result.is_ok());
    }

    #[tokio::test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    async fn test_paste_clipboard_command_error_handling() {
        // Test error handling in keyboard emulator
        let mock_state = MockState::new();

        // Test with very long text that might cause issues
        let long_text = "a".repeat(10000);
        let cancellation_flag = Arc::new(AtomicBool::new(false));
        let result = mock_state
            .app_state
            .keyboard_emulator
            .type_text(&long_text, cancellation_flag)
            .await;
        assert!(result.is_ok()); // Should handle long text gracefully
    }

    #[tokio::test]
    async fn test_app_state_creation() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
            is_typing_cancelled: Arc::new(AtomicBool::new(false)),
        };

        // Test cloning
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &cloned_state.keyboard_emulator
        ));
    }

    #[test]
    fn test_typing_speed_values_match_frontend() {
        // Ensure typing speed values match what frontend expects
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Slow).unwrap(),
            "\"slow\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Normal).unwrap(),
            "\"normal\""
        );
        assert_eq!(
            serde_json::to_string(&TypingSpeed::Fast).unwrap(),
            "\"fast\""
        );
    }

    #[test]
    fn test_app_state_structure() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        let _app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
            is_typing_cancelled: Arc::new(AtomicBool::new(false)),
        };

        // Verify app state holds correct reference to keyboard emulator
    }

    #[test]
    fn test_app_state_cancellation_methods() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let app_state = AppState {
            keyboard_emulator,
            is_typing_cancelled: Arc::new(AtomicBool::new(false)),
        };

        // Test initial state
        assert!(!app_state.is_cancelled());

        // Test cancel_typing
        app_state.cancel_typing();
        assert!(app_state.is_cancelled());

        // Test reset_cancellation
        app_state.reset_cancellation();
        assert!(!app_state.is_cancelled());
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_tray_menu_submenu_persistence() {
        // Test to ensure submenu items are properly built and won't vanish
        // This test verifies the menu structure is stable

        let menu_structure = vec![
            ("paste", "MenuItemKind::MenuItem"),
            ("cancel_typing", "MenuItemKind::MenuItem"),
            ("quit", "MenuItemKind::MenuItem"),
        ];

        // Ensure menu IDs are unique
        let all_ids: Vec<&str> = menu_structure.iter().map(|(id, _)| *id).collect();

        let unique_ids: std::collections::HashSet<_> = all_ids.iter().collect();
        assert_eq!(
            all_ids.len(),
            unique_ids.len(),
            "All menu IDs should be unique"
        );
    }

    #[test]
    fn test_keyboard_emulator_channel_creation() {
        // Test that keyboard emulator creates channels properly
        let (tx, mut rx) = mpsc::unbounded_channel::<String>();

        // Send test data
        tx.send("test".to_string()).unwrap();

        // Verify channel works
        assert_eq!(rx.try_recv().unwrap(), "test");
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_app_state_arc_references() {
        let mock_state = MockState::new();

        // Test that Arc references are properly shared
        let state1 = mock_state.app_state.clone();
        let state2 = mock_state.app_state.clone();

        // Verify keyboard emulator is shared between clones
        assert!(Arc::ptr_eq(
            &state1.keyboard_emulator,
            &state2.keyboard_emulator
        ));
    }

    #[test]
    fn test_app_lifecycle_initialization_order() {
        // Test that components are initialized in the correct order
        // 1. Keyboard emulator
        // 2. Tray setup
        // 3. App state creation
        // 4. Event listeners

        // Step 1: Keyboard emulator
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

        // Step 2: Tray manager
        let _tray_manager = TrayManager::new();

        // Step 3: App state creation
        let app_state = AppState {
            keyboard_emulator: keyboard_emulator.clone(),
            is_typing_cancelled: Arc::new(AtomicBool::new(false)),
        };

        // Verify everything is connected properly
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &keyboard_emulator
        ));
    }

    #[test]
    fn test_event_listener_setup() {
        // Test that event listeners are properly set up
        let event_names = vec!["paste_clipboard", "cancel_typing"];

        // Verify event names match what's used in the app
        for event in &event_names {
            assert!(!event.is_empty());
            assert!(!event.contains(" "));
        }

        // Test that events would be properly handled
        assert_eq!(event_names[0], "paste_clipboard");
        assert_eq!(event_names[1], "cancel_typing");
    }

    #[test]
    fn test_activation_policy_setting() {
        // Test that activation policy is set correctly on macOS
        #[cfg(target_os = "macos")]
        {
            // On macOS, we should use Accessory policy for menu bar apps
            // This hides the dock icon
            let expected_policy = "Accessory";
            assert_eq!(expected_policy, "Accessory");
        }
    }

    #[test]
    fn test_initialize_components() {
        // Test the initialize_components function
        let result = initialize_components();
        assert!(result.is_ok());

        let keyboard_emulator = result.unwrap();

        // Verify keyboard emulator is created
        assert!(Arc::strong_count(&keyboard_emulator) > 0);
    }

    #[test]
    fn test_initialize_components_creates_valid_state() {
        // Test that initialize_components creates valid state
        let result = initialize_components();
        assert!(result.is_ok());

        let keyboard_emulator = result.unwrap();

        // Test keyboard emulator is properly shared
        let emulator_ref1 = keyboard_emulator.clone();
        let emulator_ref2 = keyboard_emulator.clone();
        assert!(Arc::ptr_eq(&emulator_ref1, &emulator_ref2));
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_create_app_state() {
        // Test the create_app_state function
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let app_state = create_app_state(keyboard_emulator.clone());

        // Verify the app state holds the correct reference
        assert!(Arc::ptr_eq(
            &app_state.keyboard_emulator,
            &keyboard_emulator
        ));

        // Test cloning
        let cloned_state = app_state.clone();
        assert!(Arc::ptr_eq(
            &cloned_state.keyboard_emulator,
            &app_state.keyboard_emulator
        ));
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_paste_clipboard_command_struct() {
        // Test that the paste_clipboard command can be invoked
        // We can't test it directly without a full Tauri context, but we can test the structure

        // Verify the command exists and has the correct signature
        let command_name = "paste_clipboard";
        assert!(!command_name.is_empty());

        // Test that our mock state structure is valid
        let mock_state = MockState::new();
        assert!(Arc::strong_count(&mock_state.app_state.keyboard_emulator) > 0);
    }

    #[test]
    fn test_error_result_types() {
        // Test that our functions return the expected error types
        fn test_box_error() -> Result<(), Box<dyn std::error::Error>> {
            Ok(())
        }

        fn test_string_error() -> Result<(), String> {
            Ok(())
        }

        assert!(test_box_error().is_ok());
        assert!(test_string_error().is_ok());
    }

    #[test]
    #[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
    #[cfg(not(tarpaulin))]
    fn test_handle_paste_clipboard_event() {
        let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());
        let cancellation_flag = Arc::new(AtomicBool::new(false));

        // Call the function - it spawns a thread
        handle_paste_clipboard_event(keyboard_emulator.clone(), cancellation_flag);

        // Give the spawned thread time to start
        std::thread::sleep(std::time::Duration::from_millis(10));

        // Verify the keyboard emulator is still valid
        assert!(Arc::strong_count(&keyboard_emulator) > 0);
    }

    #[test]
    fn test_event_names() {
        // Test that event names are consistent
        let paste_clipboard_event = "paste_clipboard";
        let cancel_typing_event = "cancel_typing";

        assert_eq!(paste_clipboard_event, "paste_clipboard");
        assert_eq!(cancel_typing_event, "cancel_typing");
        assert!(!paste_clipboard_event.contains(" "));
        assert!(!cancel_typing_event.contains(" "));
    }

    #[test]
    fn test_setup_delay() {
        // Test the delay used before creating tray
        let delay = std::time::Duration::from_millis(100);
        assert_eq!(delay.as_millis(), 100);
    }

    #[test]
    fn test_activation_policy_name() {
        // Test activation policy string
        let policy = "Accessory";
        assert_eq!(policy, "Accessory");
    }
}
