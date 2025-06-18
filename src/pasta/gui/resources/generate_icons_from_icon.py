"""Generate icons from icon.png for Pasta application."""

import os
import subprocess

from PIL import Image
from PIL.Image import Image as PILImage


def create_icon_set_from_logo(logo_path: str) -> None:
    """Create all required icons from the icon.

    Args:
        logo_path: Path to the icon.png file
    """
    # Load the logo
    logo: PILImage = Image.open(logo_path)

    # Convert to RGBA if not already
    if logo.mode != "RGBA":
        logo = logo.convert("RGBA")

    # Standard sizes for various platforms
    sizes = [16, 32, 64, 128, 256, 512]

    # Generate regular icons
    for size in sizes:
        # Resize using high-quality resampling
        icon = logo.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(f"pasta_{size}.png")
        print(f"Generated pasta_{size}.png")

    # Generate disabled/grayscale versions
    for size in sizes:
        icon = logo.resize((size, size), Image.Resampling.LANCZOS)
        # Convert to grayscale while preserving alpha
        gray = icon.convert("LA").convert("RGBA")
        gray.save(f"pasta_disabled_{size}.png")
        print(f"Generated pasta_disabled_{size}.png")

    # Create default icon (64x64)
    default_icon = logo.resize((64, 64), Image.Resampling.LANCZOS)
    default_icon.save("pasta.png")
    print("Generated pasta.png")

    # Create Windows .ico file (multiple sizes)
    # Windows .ico files can contain multiple resolutions
    # We resize to the largest size and let PIL handle the multi-resolution icon
    icon_256 = logo.resize((256, 256), Image.Resampling.LANCZOS)

    # Save as .ico with multiple resolutions
    icon_256.save("pasta.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Generated pasta.ico")

    # Create macOS .icns file if on macOS
    if os.path.exists("/usr/bin/iconutil"):
        create_macos_icns(logo)

    print("\nAll icons generated successfully!")


def create_macos_icns(logo: Image.Image) -> None:
    """Create macOS .icns file from logo.

    Args:
        logo: PIL Image object of the logo
    """
    # Create iconset directory
    iconset_dir = "pasta.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    # macOS icon sizes (with @2x variants)
    macos_sizes = [
        (16, "16x16"),
        (32, "16x16@2x"),
        (32, "32x32"),
        (64, "32x32@2x"),
        (128, "128x128"),
        (256, "128x128@2x"),
        (256, "256x256"),
        (512, "256x256@2x"),
        (512, "512x512"),
        (1024, "512x512@2x"),
    ]

    for size, name in macos_sizes:
        icon = logo.resize((size, size), Image.Resampling.LANCZOS)
        icon.save(f"{iconset_dir}/icon_{name}.png")

    # Use iconutil to create .icns file
    try:
        subprocess.run(["/usr/bin/iconutil", "-c", "icns", "-o", "pasta.icns", iconset_dir], check=True)
        print("Generated pasta.icns")

        # Clean up iconset directory
        import shutil

        shutil.rmtree(iconset_dir)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create .icns file: {e}")


def main() -> None:
    """Generate all required icons from icon."""
    logo_path = "icon.png"  # Use icon.png for app icons (no text)

    if not os.path.exists(logo_path):
        print(f"Error: {logo_path} not found!")
        print("Make sure icon.png is in the same directory as this script.")
        return

    create_icon_set_from_logo(logo_path)


if __name__ == "__main__":
    main()
