"""Platform-specific utility functions."""

import platform


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
