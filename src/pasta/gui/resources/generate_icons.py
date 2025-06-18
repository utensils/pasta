"""Generate icons for Pasta application."""

from typing import Union

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from PIL.ImageFont import ImageFont as DefaultImageFont


def create_pasta_icon(size: int, enabled: bool = True) -> Image.Image:
    """Create a Pasta icon.

    Args:
        size: Icon size (width and height)
        enabled: Whether to create enabled or disabled version

    Returns:
        PIL Image
    """
    # Create image with transparent background
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Define colors
    if enabled:
        bg_color = (52, 120, 246)  # Blue
        fg_color = (255, 255, 255)  # White
    else:
        bg_color = (150, 150, 150)  # Gray
        fg_color = (255, 255, 255)  # White

    # Draw rounded rectangle background
    padding = size // 8
    draw.rounded_rectangle([padding, padding, size - padding, size - padding], radius=size // 6, fill=bg_color)

    # Draw "P" letter
    try:
        # Try to use a nice font
        font_size = size // 2
        font: Union[FreeTypeFont, DefaultImageFont] = ImageFont.truetype("Arial.ttf", font_size)
    except Exception:
        # Fall back to default font
        font = ImageFont.load_default()

    # Center the text
    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 16  # Slight adjustment

    draw.text((x, y), text, fill=fg_color, font=font)

    return image


def main() -> None:
    """Generate all required icons."""
    # Standard sizes
    sizes = [16, 32, 64, 128, 256]

    for size in sizes:
        # Enabled icon
        icon = create_pasta_icon(size, enabled=True)
        icon.save(f"pasta_{size}.png")

        # Disabled icon
        icon_disabled = create_pasta_icon(size, enabled=False)
        icon_disabled.save(f"pasta_disabled_{size}.png")

    # Create default icon
    default_icon = create_pasta_icon(64, enabled=True)
    default_icon.save("pasta.png")

    print("Icons generated successfully!")


if __name__ == "__main__":
    main()
