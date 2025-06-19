# Safe Testing Guidelines

This document explains how to run tests without interfering with your system.

## Problem Tests

Some integration tests might interfere with your system by:
1. Opening System Preferences (even though we try to mock it)
2. Registering actual keyboard hotkeys
3. Starting clipboard monitoring threads
4. Creating system tray icons

## Solutions Implemented

### 1. Global Mocking (in `tests/conftest.py`)
- **keyboard module**: Globally mocked to prevent actual hotkey registration
- **pyautogui module**: Globally mocked to prevent actual keyboard/mouse input
- **subprocess.run**: Intercepted to block System Preferences from opening
- **Qt environment**: Set to `QT_QPA_PLATFORM=offscreen` for headless operation

### 2. Running Tests Safely

To run tests without system interference:

```bash
# Run all tests except potentially interfering ones
uv run pytest -m "not system_interfering"

# Run only unit tests (safest)
uv run pytest tests/unit/

# Run specific safe test files
uv run pytest tests/unit/test_settings.py tests/unit/test_storage.py

# Skip integration tests that might cause issues
uv run pytest --ignore=tests/integration/test_app_launch.py
```

### 3. Identifying Problem Tests

Run the isolation test to verify mocking is working:
```bash
uv run pytest tests/test_system_isolation.py -v
```

### 4. Known Problematic Test Files

These tests might still cause issues despite mocking:

1. **tests/integration/test_app_launch.py**
   - Creates real component instances
   - Might start background threads

2. **tests/integration/test_tray_integration.py**
   - Creates SystemTray instances
   - Might register hotkeys

3. **Any test creating real HotkeyManager instances**
   - Even with mocked keyboard module, might cause issues

## Recommendations

1. **For local development**, run:
   ```bash
   uv run pytest tests/unit/ -v
   ```

2. **For CI/CD**, all tests should work fine in headless environments

3. **If you experience interference**, add the problematic test to this list and mark it with:
   ```python
   @pytest.mark.system_interfering
   @pytest.mark.skip(reason="TODO: Properly isolate this test from system")
   def test_something():
       pass
   ```

## Debugging Tips

If a test is still interfering:

1. Check if it's creating real instances without mocking:
   ```python
   # Bad
   manager = HotkeyManager()

   # Good
   with patch('pasta.core.hotkeys.HotkeyManager') as mock:
       manager = mock()
   ```

2. Check for subprocess calls:
   ```python
   # These should be mocked automatically, but double-check
   subprocess.run(['osascript', '-e', 'tell app...'])
   ```

3. Look for thread starts:
   ```python
   # Threads might bypass mocks
   thread = Thread(target=some_function)
   thread.start()  # This might cause issues
   ```

## Running Tests in CI

CI environments should be safe as they:
- Run headless (no GUI)
- Don't have accessibility permissions
- Can't open System Preferences

The test suite is designed to work in CI without issues.
