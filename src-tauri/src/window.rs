use tauri::{AppHandle, CloseRequestApi, Manager, WebviewWindowBuilder, WindowEvent};

/// Creates and configures the settings window
pub fn create_settings_window(app: &AppHandle) -> tauri::Result<()> {
    let window = WebviewWindowBuilder::new(
        app,
        "main",
        tauri::WebviewUrl::App("index.html".into()),
    )
    .title("Pasta Settings")
    .inner_size(400.0, 300.0)
    .resizable(false)
    .visible(false) // Start hidden to prevent flash
    .build()?;

    // Configure window behavior
    #[cfg(target_os = "macos")]
    {
        // Show dock icon when window is open
        let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
    }

    // Show the window after configuration
    window.show()?;
    window.set_focus()?;

    // Handle window close event
    let app_handle = app.clone();
    window.on_window_event(move |event| {
        if let WindowEvent::CloseRequested { api, .. } = event {
            handle_window_close_request(api, &app_handle);
        }
    });

    Ok(())
}

/// Handles the window close request by hiding instead of closing
fn handle_window_close_request(api: &CloseRequestApi, app: &AppHandle) {
    // Prevent default close behavior
    api.prevent_close();
    
    // Hide the window instead of closing
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.hide();
        
        #[cfg(target_os = "macos")]
        {
            // Hide dock icon when no windows are visible
            let _ = app.set_activation_policy(tauri::ActivationPolicy::Accessory);
        }
    }
}

/// Shows the settings window, creating it if necessary
pub fn show_settings_window(app: &AppHandle) -> tauri::Result<()> {
    if let Some(window) = app.get_webview_window("main") {
        #[cfg(target_os = "macos")]
        {
            // Show dock icon when window is being shown
            let _ = app.set_activation_policy(tauri::ActivationPolicy::Regular);
        }
        
        window.show()?;
        window.set_focus()?;
    } else {
        // Create settings window if it doesn't exist
        create_settings_window(app)?;
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_window_module_compiles() {
        // Basic compilation test
        assert!(true);
    }
    
    // Note: Full window behavior tests would require a running Tauri app context
    // which is difficult to test in unit tests. These behaviors are better tested
    // through integration tests or manual testing.
}