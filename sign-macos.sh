#!/bin/bash
set -e

# Script to self-sign Pasta app for macOS
# This helps reduce security warnings without an Apple Developer account

echo "🔏 macOS Self-Signing Script for Pasta"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script only works on macOS${NC}"
    exit 1
fi

# Function to find available code signing certificates
find_certificates() {
    echo -e "${YELLOW}Looking for code signing certificates...${NC}"
    security find-identity -v -p codesigning | grep -E "^[[:space:]]+[0-9]+\)"
}

# Check command line arguments
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <certificate-name|adhoc> [target]"
    echo "  certificate-name: Name of your code signing certificate"
    echo "                   Use 'adhoc' for ad-hoc signing (no certificate needed)"
    echo "  target: Optional target architecture (x86_64-apple-darwin or aarch64-apple-darwin)"
    echo ""
    echo "Available certificates:"
    find_certificates
    echo ""
    echo "For ad-hoc signing (simplest option):"
    echo "  $0 adhoc"
    echo ""
    echo "To create a self-signed certificate:"
    echo "1. Open Keychain Access"
    echo "2. Certificate Assistant > Create a Certificate"
    echo "3. Name: 'Your Name', Type: 'Code Signing'"
    echo "4. Check 'Let me override defaults' and follow prompts"
    exit 1
fi

CERT_NAME="$1"
TARGET="${2:-}"

# Handle ad-hoc signing or certificate signing
if [ "$CERT_NAME" = "adhoc" ]; then
    echo -e "${GREEN}✓ Using ad-hoc signing (no certificate required)${NC}"
    SIGN_IDENTITY="-"
else
    # Verify certificate exists
    if ! security find-identity -v -p codesigning | grep -q "$CERT_NAME"; then
        echo -e "${RED}Error: Certificate '$CERT_NAME' not found${NC}"
        echo ""
        echo "Available certificates:"
        find_certificates
        exit 1
    fi
    echo -e "${GREEN}✓ Found certificate: $CERT_NAME${NC}"
    SIGN_IDENTITY="$CERT_NAME"
fi

# Determine paths based on target
if [ -n "$TARGET" ]; then
    BUNDLE_PATH="src-tauri/target/$TARGET/release/bundle"
else
    # Try to find the bundle path
    if [ -d "src-tauri/target/release/bundle" ]; then
        BUNDLE_PATH="src-tauri/target/release/bundle"
    elif [ -d "src-tauri/target/aarch64-apple-darwin/release/bundle" ]; then
        BUNDLE_PATH="src-tauri/target/aarch64-apple-darwin/release/bundle"
    elif [ -d "src-tauri/target/x86_64-apple-darwin/release/bundle" ]; then
        BUNDLE_PATH="src-tauri/target/x86_64-apple-darwin/release/bundle"
    else
        echo -e "${RED}Error: Could not find bundle directory${NC}"
        echo "Make sure to build the app first with: cargo tauri build"
        exit 1
    fi
fi

MACOS_PATH="$BUNDLE_PATH/macos"
APP_NAME="Pasta.app"

# Check if the app exists
if [ ! -d "$MACOS_PATH/$APP_NAME" ]; then
    echo -e "${RED}Error: App not found at $MACOS_PATH/$APP_NAME${NC}"
    echo "Make sure to build the app first with: cargo tauri build"
    exit 1
fi

echo -e "${YELLOW}Signing $APP_NAME...${NC}"

# Sign the app bundle with deep signing for all embedded content
codesign --force --deep --sign "$SIGN_IDENTITY" "$MACOS_PATH/$APP_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully signed $APP_NAME${NC}"
else
    echo -e "${RED}✗ Failed to sign $APP_NAME${NC}"
    exit 1
fi

# Verify the signature
echo -e "${YELLOW}Verifying signature...${NC}"
codesign -dv "$MACOS_PATH/$APP_NAME" 2>&1

# Check gatekeeper status
echo -e "${YELLOW}Checking Gatekeeper status...${NC}"
spctl -a -vv "$MACOS_PATH/$APP_NAME" 2>&1 || true

echo ""
echo -e "${GREEN}✓ Signing complete!${NC}"
echo ""
echo "The signed app is located at:"
echo "  $MACOS_PATH/$APP_NAME"
echo ""
echo "Note: Self-signed apps may still trigger security warnings on first run,"
echo "but they should be less intrusive than unsigned apps."
echo ""
echo "To create a DMG with the signed app, the tauri build process"
echo "should automatically include it in the .dmg file."