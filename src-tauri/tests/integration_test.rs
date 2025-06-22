use std::sync::{atomic::AtomicBool, Arc};

use pasta_tray_lib::{
    create_app_state, initialize_components,
    keyboard::{KeyboardEmulator, TypingSpeed},
};

#[test]
#[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
fn test_keyboard_integration() {
    // Test that keyboard emulator works
    let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

    // Keyboard emulator should be created successfully
    assert!(Arc::strong_count(&keyboard_emulator) >= 1);
}

#[tokio::test]
#[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
async fn test_keyboard_emulator_async_operations() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();

    // Test multiple async operations
    let result1 = keyboard_emulator
        .type_text("Hello", Arc::new(AtomicBool::new(false)))
        .await;
    assert!(result1.is_ok());

    let result2 = keyboard_emulator
        .type_text("World", Arc::new(AtomicBool::new(false)))
        .await;
    assert!(result2.is_ok());

    // Test with special characters
    let result3 = keyboard_emulator
        .type_text("Line1\nLine2\tTabbed", Arc::new(AtomicBool::new(false)))
        .await;
    assert!(result3.is_ok());
}

#[test]
fn test_typing_speed_consistency_across_modules() {
    // Ensure TypingSpeed enum is consistent across modules
    let speeds = vec![TypingSpeed::Slow, TypingSpeed::Normal, TypingSpeed::Fast];

    for speed in speeds {
        // Test serialization roundtrip
        let json = serde_json::to_string(&speed).unwrap();
        let deserialized: TypingSpeed = serde_json::from_str(&json).unwrap();
        assert_eq!(speed, deserialized);

        // Test that delay values are sensible
        let delay = speed.delay_ms();
        assert!(delay >= 10 && delay <= 50);
    }
}

#[test]
fn test_concurrent_operations() {
    use std::thread;

    let keyboard_emulator = Arc::new(KeyboardEmulator::new().unwrap());

    let mut handles = vec![];

    // Spawn multiple threads that use the keyboard emulator
    for i in 0..3 {
        let ke = keyboard_emulator.clone();
        let handle = thread::spawn(move || {
            // Just verify we can clone and hold references
            let _local_ref = ke.clone();
            format!("Thread {} completed", i)
        });
        handles.push(handle);
    }

    // All threads should complete without issue
    for handle in handles {
        let result = handle.join().unwrap();
        assert!(result.contains("completed"));
    }
}

#[test]
fn test_error_handling() {
    // Test error handling when components fail
    // Since we removed config, there are fewer failure modes

    // Keyboard emulator should handle errors gracefully
    let result = KeyboardEmulator::new();
    assert!(result.is_ok());
}

#[tokio::test]
#[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
async fn test_keyboard_emulator_channel_capacity() {
    let keyboard_emulator = KeyboardEmulator::new().unwrap();

    // Send multiple commands quickly
    let mut results = vec![];
    for i in 0..5 {
        let result = keyboard_emulator
            .type_text(&format!("Text {}", i), Arc::new(AtomicBool::new(false)))
            .await;
        results.push(result);
    }

    // All should succeed
    for result in results {
        assert!(result.is_ok());
    }
}

#[test]
#[ignore = "Creates real keyboard emulator that can type on system - run with --ignored flag"]
fn test_full_app_initialization() {
    // Test the complete initialization flow using public API
    let result = initialize_components();
    assert!(result.is_ok());

    let keyboard_emulator = result.unwrap();

    // Verify component is properly initialized
    assert!(Arc::strong_count(&keyboard_emulator) > 0);

    // Create app state
    let app_state = create_app_state(keyboard_emulator.clone());

    // Verify app state is properly created
    assert!(!app_state.is_cancelled());
}
