"""Permission checking and management."""

import os
import platform
import subprocess
import threading
from typing import Optional

try:
    import grp

    HAS_GRP = True
except ImportError:
    grp = None  # type: ignore[assignment]  # Not available on Windows
    HAS_GRP = False


class PermissionChecker:
    """Checks and manages system permissions.

    This class handles checking for required system permissions
    on different platforms and guides users to enable them.

    Attributes:
        platform: Current platform name
    """

    def __init__(self) -> None:
        """Initialize the PermissionChecker."""
        self.platform = platform.system()
        self._permission_lock = threading.Lock()
        self._cached_result: Optional[bool] = None

    def check_permissions(self) -> bool:
        """Check if necessary permissions are granted.

        Returns:
            True if permissions are granted, False otherwise
        """
        # Check cache first
        with self._permission_lock:
            if self._cached_result is not None:
                return self._cached_result

        # Platform-specific checks
        if self.platform == "Darwin":
            result = self._check_macos_accessibility()
        elif self.platform == "Windows":
            result = self._check_windows_permissions()
        elif self.platform == "Linux":
            result = self._check_linux_permissions()
        else:
            # Unknown platform - assume permissions are OK
            result = True

        # Cache result
        with self._permission_lock:
            self._cached_result = result

        return result

    def _check_macos_accessibility(self) -> bool:
        """Check macOS accessibility permissions.

        Returns:
            True if accessibility permissions are granted
        """
        try:
            # AppleScript to check accessibility permissions
            script = """
            tell application "System Events"
                set isEnabled to UI elements enabled
            end tell
            return isEnabled
            """

            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)

            return result.stdout.strip().lower() == "true"
        except (subprocess.SubprocessError, OSError):
            return False

    def _check_windows_permissions(self) -> bool:
        """Check Windows permissions.

        Returns:
            True - Windows doesn't require special permissions for our use case
        """
        # Windows doesn't require special permissions for keyboard simulation
        return True

    def _check_linux_permissions(self) -> bool:
        """Check Linux permissions.

        Returns:
            True if user has necessary permissions
        """
        # Check if user is in input group (for device access)
        if not HAS_GRP:
            return True  # Can't check without grp module, assume OK

        try:
            # Type assertion for mypy - we know grp is not None here
            assert grp is not None
            input_group = grp.getgrnam("input")
            user_groups = os.getgroups()
            return input_group.gr_gid in user_groups
        except KeyError:
            # Input group doesn't exist - not required
            return True
        except Exception:
            return True  # On error, assume permissions are OK

    def request_permissions(self) -> None:
        """Request necessary permissions from the user."""
        if self.platform == "Darwin":
            self._request_macos_accessibility()
        elif self.platform == "Linux":
            self._request_linux_permissions()
        # Windows doesn't need permission requests

    def _request_macos_accessibility(self) -> None:
        """Open macOS accessibility preferences."""
        try:
            script = """
            tell application "System Preferences"
                activate
                reveal anchor "Privacy_Accessibility" of pane id "com.apple.preference.security"
            end tell
            """
            subprocess.run(["osascript", "-e", script], check=False)
        except (subprocess.SubprocessError, OSError):
            pass

    def _request_linux_permissions(self) -> None:
        """Print instructions for Linux permission setup."""
        print("To use Pasta on Linux, you may need to add your user to the 'input' group:")
        print("  sudo usermod -a -G input $USER")
        print("Then log out and back in for the changes to take effect.")

    def get_permission_error_message(self) -> str:
        """Get user-friendly error message for permission issues.

        Returns:
            Platform-specific error message
        """
        if self.platform == "Darwin":
            return (
                "Pasta requires accessibility permissions to simulate keyboard input. "
                "Please grant permission in System Preferences > Security & Privacy > "
                "Privacy > Accessibility."
            )
        elif self.platform == "Linux":
            return "Pasta may require your user to be in the 'input' group to access input devices. Run: sudo usermod -a -G input $USER"
        else:
            return "Permission error occurred."

    def get_permission_instructions(self) -> str:
        """Get detailed permission setup instructions.

        Returns:
            Platform-specific setup instructions
        """
        if self.platform == "Darwin":
            return (
                "macOS Accessibility Setup:\n"
                "1. Open System Preferences\n"
                "2. Go to Security & Privacy > Privacy > Accessibility\n"
                "3. Click the lock to make changes\n"
                "4. Add Pasta to the list and check the box\n"
                "5. Restart Pasta"
            )
        elif self.platform == "Linux":
            return (
                "Linux Permission Setup:\n"
                "1. Add your user to the input group:\n"
                "   sudo usermod -a -G input $USER\n"
                "2. Log out and back in\n"
                "3. Verify with: groups | grep input"
            )
        elif self.platform == "Windows":
            return "Windows Setup:\nNo special permissions required for keyboard simulation."
        else:
            return f"{self.platform} platform detected. No specific instructions available."

    def create_info_plist(self) -> str:
        """Generate Info.plist content for macOS.

        Returns:
            Info.plist XML content
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Pasta</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.pasta</string>
    <key>NSAccessibilityUsageDescription</key>
    <string>Pasta requires accessibility permissions to simulate keyboard input.</string>
</dict>
</plist>"""

    def create_manifest(self) -> str:
        """Generate Windows manifest for UAC.

        Returns:
            Windows manifest XML content
        """
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>"""

    def is_wayland(self) -> bool:
        """Check if running under Wayland on Linux.

        Returns:
            True if Wayland session detected
        """
        if self.platform != "Linux":
            return False
        return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

    def get_linux_setup_script(self) -> str:
        """Get Linux permission setup script.

        Returns:
            Shell script for Linux setup
        """
        return """#!/bin/bash
# Add user to input group for device access
sudo usermod -a -G input $USER

# Install required packages
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "Installing Wayland tools..."
    sudo apt-get install -y ydotool
else
    echo "Installing X11 tools..."
    sudo apt-get install -y xdotool xclip
fi

echo "Please log out and back in for group changes to take effect."
"""

    def get_linux_distro(self) -> str:
        """Detect Linux distribution.

        Returns:
            Distribution name or "Unknown"
        """
        if self.platform != "Linux":
            return ""

        try:
            # Try to read from os-release file
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("NAME="):
                        return line.split("=")[1].strip().strip('"')
        except Exception:
            pass

        return "Unknown"
