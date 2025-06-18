#!/bin/bash
# Build script for macOS app bundle

echo "Building Pasta for macOS..."

# Ensure we're in the project root
cd "$(dirname "$0")/.." || exit 1

# Install dependencies if not already installed
echo "Installing dependencies..."
uv sync --all-extras

# Run tests first
echo "Running tests..."
uv run pytest tests/unit/test_macos_ui_simple.py -q

# Build with PyInstaller
echo "Building app bundle..."
uv run pyinstaller pasta.spec --clean --noconfirm

# Check if build succeeded
if [ -d "dist/Pasta.app" ]; then
    echo "✅ Build successful! App bundle created at dist/Pasta.app"

    # Show bundle info
    echo ""
    echo "Bundle information:"
    echo "-------------------"
    defaults read "$(pwd)/dist/Pasta.app/Contents/Info.plist" CFBundleName 2>/dev/null || echo "CFBundleName: Not found"
    defaults read "$(pwd)/dist/Pasta.app/Contents/Info.plist" LSUIElement 2>/dev/null || echo "LSUIElement: Not found"

    echo ""
    echo "To install:"
    echo "  cp -r dist/Pasta.app /Applications/"
    echo ""
    echo "To run:"
    echo "  open dist/Pasta.app"
else
    echo "❌ Build failed!"
    exit 1
fi
