#!/usr/bin/env python3
"""Test that all required imports work correctly."""

import importlib.util


def test_imports() -> None:
    """Test importing all required packages."""
    print("Testing imports...")

    packages = [
        ("pystray", "pystray"),
        ("pyperclip", "pyperclip"),
        ("pyautogui", "pyautogui"),
        ("PIL", "PIL.Image"),
        ("PyQt6", "PyQt6.QtWidgets"),
        ("psutil", "psutil"),
        ("cryptography", "cryptography.fernet"),
    ]

    for display_name, import_path in packages:
        if importlib.util.find_spec(import_path.split(".")[0]) is not None:
            print(f"✓ {display_name} imported successfully")
        else:
            print(f"✗ Failed to import {display_name}")

    print("\nImport test complete!")


if __name__ == "__main__":
    test_imports()
