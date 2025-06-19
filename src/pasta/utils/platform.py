"""Platform-specific utility functions."""

import platform
import subprocess


def get_platform() -> str:
    """Get the current platform name.

    Returns:
        Platform name ('Darwin', 'Windows', or 'Linux')
    """
    return platform.system()


def get_paste_key() -> str:
    """Get platform-specific paste modifier key.

    Returns:
        'cmd' for macOS, 'ctrl' for others
    """
    return "cmd" if get_platform() == "Darwin" else "ctrl"


def get_platform_info() -> dict:
    """Get detailed platform information.

    Returns:
        Dictionary with platform details
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def get_active_window_title() -> str:
    """Get the title of the currently active window.

    Returns:
        Title of the active window or empty string if unable to determine
    """
    system = get_platform()

    try:
        if system == "Darwin":  # macOS
            script = """
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                tell process frontApp
                    if exists (window 1) then
                        return name of window 1
                    else
                        return frontApp
                    end if
                end tell
            end tell
            """
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1)
            return result.stdout.strip() if result.returncode == 0 else ""

        elif system == "Linux":
            # Try xdotool first
            result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                return result.stdout.strip()

            # Fallback to wmctrl
            result = subprocess.run(["wmctrl", "-lp"], capture_output=True, text=True, timeout=1)
            if result.returncode == 0:
                # Parse active window from wmctrl output
                # This is a simplified approach
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if " * " in line:  # Active window marker
                        parts = line.split(None, 4)
                        if len(parts) >= 5:
                            return parts[4]
            return ""

        elif system == "Windows":
            # Use ctypes to get active window title
            try:
                import ctypes

                user32 = ctypes.windll.user32  # type: ignore[attr-defined]

                hwnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(hwnd) + 1
                buffer = ctypes.create_unicode_buffer(length)
                user32.GetWindowTextW(hwnd, buffer, length)

                return buffer.value
            except Exception:
                return ""

    except Exception:
        return ""

    return ""
