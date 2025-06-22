# macOS Code Signing Guide for Pasta

This guide explains how to sign the Pasta app on macOS without an Apple Developer account.

## Why Sign?

Signing reduces security warnings when users first run Pasta. While not as trusted as an Apple Developer certificate, it's better than completely unsigned apps.

## Quick Start (Ad-hoc Signing)

The simplest approach is ad-hoc signing, which requires no certificate:

```bash
# Build the app
cargo tauri build

# Sign with ad-hoc signature
./sign-macos.sh adhoc
```

That's it! The app is now signed and ready to use.

## Prerequisites

- macOS (this only works on Mac)
- Pasta built with `cargo tauri build`

## Step 1: Create a Self-Signed Certificate

1. Open **Keychain Access** (found in Applications > Utilities)
2. In the menu bar, go to **Keychain Access > Certificate Assistant > Create a Certificate**
3. Fill in the certificate details:
   - **Name**: Enter your name (e.g., "James Brink")
   - **Identity Type**: Self Signed Root
   - **Certificate Type**: Code Signing
   - ✅ Check **"Let me override defaults"**
4. Click **Continue** through all the screens, using default values
5. On the "Specify a Location" screen, ensure **Keychain** is set to "login"
6. Click **Create**

## Step 2: Build Pasta

```bash
cargo tauri build
```

This creates the unsigned .app bundle in the build directory.

## Step 3: Sign the App

Use the provided signing script:

```bash
./sign-macos.sh "Your Name"
```

Replace "Your Name" with the exact name you used for the certificate.

For specific architectures:
```bash
# Intel Macs
./sign-macos.sh "Your Name" x86_64-apple-darwin

# Apple Silicon Macs
./sign-macos.sh "Your Name" aarch64-apple-darwin
```

## Step 4: Verify Signing

The script automatically verifies the signature. You should see output like:
```
✓ Successfully signed Pasta.app
Executable=/path/to/Pasta.app/Contents/MacOS/Pasta
Identifier=com.pasta.app
Format=app bundle with Mach-O universal
Signed=123456
```

## Troubleshooting

### "Certificate not found"
- Ensure the certificate name matches exactly (case-sensitive)
- Run `security find-identity -v -p codesigning` to list available certificates

### "App not found"
- Make sure you've run `cargo tauri build` first
- Check the target architecture matches your build

### Still getting security warnings?
- Self-signed certificates still trigger warnings, but they're less severe
- Users can open the app normally instead of right-clicking
- For zero warnings, you need an Apple Developer account ($99/year)

## Notes

- Self-signed certificates are stored in your login keychain
- They don't expire for 365 days by default
- You can delete them anytime from Keychain Access
- This signing is only for local/personal distribution
- For App Store or notarization, you need an Apple Developer account