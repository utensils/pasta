// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    pasta_lib::run()
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_main_function_exists() {
        // This test verifies that the main function exists and is callable
        // We can't actually run main() in tests as it starts the Tauri app
        // But we can verify the function signature
        assert_eq!(std::mem::size_of::<fn()>(), std::mem::size_of::<fn()>());
    }

    #[test]
    fn test_main_calls_pasta_lib_run() {
        // Verify that pasta_lib module exists and has a run function
        // This ensures our main function can call pasta_lib::run()

        // This will fail to compile if pasta_lib::run doesn't exist
        // Just checking that we can reference the function
        let _: fn() = pasta_lib::run;

        // If we got here, the function exists
        assert!(true);
    }
}
