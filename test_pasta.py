#!/usr/bin/env python3
"""Simple test script to demonstrate Pasta functionality."""

import time

import pyperclip


def test_pasta() -> None:
    """Test Pasta by copying text to clipboard."""
    print("🧪 Pasta Test Script")
    print("==================")
    print("This script will copy text to your clipboard in 5 seconds.")
    print("Make sure Pasta is running and watch it type the text!\n")

    # Countdown
    for i in range(5, 0, -1):
        print(f"Copying in {i}...")
        time.sleep(1)

    # Test text
    test_text = "Hello from Pasta! 🍝 This text was copied to clipboard and typed automatically."

    # Copy to clipboard
    pyperclip.copy(test_text)
    print(f"\n✅ Copied to clipboard: '{test_text}'")
    print("Check your active window - Pasta should be typing this text!")

    # Wait a bit
    time.sleep(3)

    # Test with multiline text
    print("\n📝 Testing multiline text in 3 seconds...")
    time.sleep(3)

    multiline_text = """This is line 1
This is line 2
This is line 3 with special chars: @#$%^&*()"""

    pyperclip.copy(multiline_text)
    print("✅ Copied multiline text!")

    time.sleep(5)

    # Test emergency stop
    print("\n🚨 Testing emergency stop - copy long text and press Double ESC to stop!")
    time.sleep(3)

    long_text = "A" * 500  # 500 A's
    pyperclip.copy(long_text)
    print("✅ Copied 500 characters - press Double ESC or click tray icon to stop!")

    print("\n✨ Test complete!")


if __name__ == "__main__":
    test_pasta()
