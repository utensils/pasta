# Pasta 🍝

A cross-platform system tray application that converts clipboard content into simulated keyboard input, bridging the gap for applications that don't support direct clipboard pasting.

## Features

- **Smart Clipboard Monitoring**: Automatically detects clipboard changes and maintains history
- **Flexible Pasting Methods**: Choose between clipboard paste or character-by-character typing
- **Cross-Platform Support**: Works on Windows, macOS, and Linux
- **Secure Storage**: Encrypts sensitive clipboard data at rest
- **Adaptive Performance**: Automatically adjusts typing speed based on system load
- **Privacy Protection**: Excludes password managers and sensitive applications
- **Rate Limiting**: Prevents abuse with configurable limits
- **System Tray Integration**: Minimal UI that stays out of your way

## Installation

### Prerequisites

- Python 3.9 or higher (3.11 recommended)
- UV package manager

### Install UV Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Pasta

```bash
# Clone the repository
git clone https://github.com/yourusername/pasta.git
cd pasta

# Install dependencies
uv sync --all-extras

# Run the application
uv run python -m pasta
```

## Platform-Specific Setup

### macOS
- Grant accessibility permissions when prompted
- System Preferences → Security & Privacy → Privacy → Accessibility

### Windows
- May require running as administrator for certain applications
- Windows Defender may need an exception added

### Linux
- Add user to the `input` group: `sudo usermod -a -G input $USER`
- Log out and back in for changes to take effect

## Usage

1. **Start Pasta**: The application runs in your system tray
2. **Copy text**: Use Ctrl+C (Cmd+C on macOS) as normal
3. **Quick Paste**: Click the tray icon or use the configured hotkey
4. **Paste from History**: Right-click tray icon → "Paste from History"

### Keyboard Shortcuts

- `Ctrl+Shift+V`: Quick paste last item
- `Ctrl+Shift+H`: Open history window
- `Ctrl+Shift+S`: Toggle monitoring

## Configuration

Access settings through the system tray menu:

- **Typing Speed**: Adjust character-per-second rate
- **History Size**: Number of clipboard entries to keep
- **Privacy Mode**: Temporarily disable all monitoring
- **Excluded Apps**: Applications to ignore for clipboard monitoring

## Development

### Setup Development Environment

```bash
# Install development dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=pasta --cov-report=html

# Run specific tests
uv run pytest -k "test_clipboard" -v
```

### Code Quality

```bash
# Linting and formatting
uv run ruff check . --fix
uv run ruff format .

# Type checking
uv run mypy src/
```

## Building

### Create Executable

```bash
# Build standalone executable
uv run pyinstaller --onefile --windowed src/pasta/__main__.py
```

### Package for Distribution

```bash
# Create distribution packages
uv build
```

## Security

- All sensitive clipboard data is encrypted using Fernet symmetric encryption
- No network connections or telemetry without explicit consent
- Secure memory cleanup on application exit
- Rate limiting prevents abuse
- Privacy mode for sensitive work

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Implement your feature
5. Run tests and ensure they pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [pystray](https://github.com/moses-palmer/pystray) for system tray integration
- Uses [PyAutoGUI](https://github.com/asweigart/pyautogui) for keyboard simulation
- Clipboard access via [pyperclip](https://github.com/asweigart/pyperclip)
- Package management with [UV](https://github.com/astral-sh/uv)

## Support

For issues, feature requests, or questions:
- Open an issue on [GitHub](https://github.com/yourusername/pasta/issues)
- Check the [troubleshooting guide](docs/troubleshooting.md)
