{
  description = "Pasta - Cross-platform clipboard manager development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    devshell.url = "github:numtide/devshell";
  };

  outputs = { self, nixpkgs, flake-utils, devshell }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ devshell.overlays.default ];
        };

        # Python 3.11 with common build dependencies
        python = pkgs.python311;
        pythonWithPackages = pkgs.python311.withPackages (ps: with ps; [
          pip
          wheel
          setuptools
        ]);

        # Build tools for native extensions
        buildTools = with pkgs; [
          # gcc is included via stdenv, no need to add it explicitly
          gnumake
          pkg-config
          openssl
          libffi
          zlib
          bzip2
          readline
          sqlite
          ncurses
          expat
          libuuid
          gdbm
          xz
          tk
        ];

        # Qt/GUI dependencies
        guiDeps = with pkgs; if pkgs.stdenv.isLinux then [
          qt6.qtbase
          qt6.qtwayland
          xorg.libX11
          xorg.libXext
          xorg.libXrender
          xorg.libXi
          xorg.libXtst
          xorg.libXcursor
          xorg.libXrandr
          xorg.libXinerama
          wayland
          libGL
          fontconfig
          freetype
        ] else if pkgs.stdenv.isDarwin then [
          # macOS Qt dependencies are handled differently
          qt6.qtbase
          libGL
          fontconfig
          freetype
        ] else [];

        # Platform-specific dependencies
        platformDeps = with pkgs; if pkgs.stdenv.isLinux then [
          # Linux-specific
          xdotool
          xclip
          wl-clipboard
          libevdev
          python311Packages.evdev
        ] else [];

        # Development tools
        devTools = with pkgs; [
          git
          curl
          wget
          jq
          ripgrep
          fd
          bat
          eza
          entr
          # For documentation
          pandoc
        ];

      in
      {
        devShells.default = pkgs.devshell.mkShell {
          name = "pasta-dev";

          # Shell prompt with project indicator
          bash = {
            interactive = ''
              PS1="\[\e[32m\]🍝 pasta-dev\[\e[0m\] \[\e[34m\]\w\[\e[0m\] $ "
            '';
          };

          # Packages available in the shell
          packages = builtins.filter (p: p != null) (with pkgs; [
            # Python and build tools
            # Use the python with packages instead of bare python to avoid conflicts
            pythonWithPackages
            uv
            ruff

            # PyInstaller dependencies
            # binutils is included via stdenv
            patchelf
            # upx  # Not available on all platforms
          ] ++ buildTools ++ guiDeps ++ platformDeps ++ devTools);

          # Environment variables
          env = [
            {
              name = "PYTHONPATH";
              eval = "$DEVSHELL_DIR/src:$PYTHONPATH";
            }
            {
              name = "LD_LIBRARY_PATH";
              eval = "${pkgs.lib.makeLibraryPath (buildTools ++ guiDeps ++ platformDeps)}:$LD_LIBRARY_PATH";
            }
            {
              name = "PKG_CONFIG_PATH";
              eval = "${pkgs.lib.makeSearchPathOutput "dev" "lib/pkgconfig" (buildTools ++ guiDeps)}:$PKG_CONFIG_PATH";
            }
            {
              name = "UV_SYSTEM_PYTHON";
              value = "1";
            }
            {
              name = "UV_PYTHON";
              value = "${python}/bin/python3.11";
            }
            {
              name = "PYTHON_KEYRING_BACKEND";
              value = "keyring.backends.null.Keyring";
            }
            # Qt environment variables
            {
              name = "QT_QPA_PLATFORM_PLUGIN_PATH";
              eval = "${pkgs.qt6.qtbase}/lib/qt-6/plugins/platforms";
            }
            {
              name = "QT_PLUGIN_PATH";
              eval = "${pkgs.qt6.qtbase}/lib/qt-6/plugins";
            }
            # For headless testing
            {
              name = "QT_QPA_PLATFORM";
              value = "offscreen";
            }
            # X11 for Linux GUI
            {
              name = "DISPLAY";
              value = ":0";
            }
          ];

          # Commands available in the shell menu
          commands = [
            # Project Management
            {
              name = "setup";
              category = "project";
              help = "Initial setup for Pasta development";
              command = ''
                echo "🍝 Setting up Pasta development environment..."

                # Install dependencies
                echo "📦 Installing dependencies..."
                uv sync --all-extras --dev

                # Install pre-commit hooks
                echo "🪝 Installing pre-commit hooks..."
                uv run pre-commit install

                echo "✅ Setup complete! Run 'menu' to see available commands."
              '';
            }
            {
              name = "run-pasta";
              category = "project";
              help = "Run Pasta application";
              command = ''
                echo "🍝 Starting Pasta..."
                # For GUI testing, might need to set platform
                export QT_QPA_PLATFORM=xcb  # or wayland
                uv run python -m pasta
              '';
            }
            {
              name = "run";
              category = "project";
              help = "Run Pasta application (alias for run-pasta)";
              command = ''
                echo "🍝 Starting Pasta..."
                # For GUI testing, might need to set platform
                export QT_QPA_PLATFORM=xcb  # or wayland
                uv run python -m pasta
              '';
            }
            {
              name = "build";
              category = "project";
              help = "Build Pasta for distribution";
              command = "uv build";
            }
            {
              name = "build-exe";
              category = "project";
              help = "Build platform-specific executable with PyInstaller";
              command = ''
                echo "📦 Building Pasta executable..."
                uv run pyinstaller --onefile --windowed \
                  --name pasta \
                  --icon src/pasta/gui/resources/pasta.ico \
                  src/pasta/__main__.py
                echo "✅ Executable built in dist/"
              '';
            }
            {
              name = "clean";
              category = "project";
              help = "Clean project artifacts";
              command = ''
                echo "🧹 Cleaning Python artifacts..."
                find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
                find . -type f -name "*.pyc" -delete
                find . -type f -name "*.pyo" -delete
                find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
                find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
                find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
                find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
                find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
                find . -type f -name ".coverage" -delete
                rm -rf build/ dist/ *.spec
                echo "✅ Clean complete!"
              '';
            }

            # Development Commands
            {
              name = "dev";
              category = "development";
              help = "Run Pasta in development mode with auto-reload";
              command = ''
                if command -v entr &> /dev/null; then
                  find src -name "*.py" | entr -r uv run python -m pasta
                else
                  echo "Install entr for auto-reload (already in shell)"
                  uv run python -m pasta
                fi
              '';
            }
            {
              name = "tray-test";
              category = "development";
              help = "Test system tray functionality";
              command = ''
                echo "🖥️ Testing system tray..."
                export QT_QPA_PLATFORM=xcb
                uv run python -c "
from pasta.gui.tray_pyside6 import SystemTray
from pasta.core.clipboard import ClipboardManager
from pasta.core.keyboard import PastaKeyboardEngine
from pasta.core.storage import StorageManager
from pasta.utils.permissions import PermissionChecker
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
clipboard = ClipboardManager()
keyboard = PastaKeyboardEngine()
storage = StorageManager()
permissions = PermissionChecker()

tray = SystemTray(clipboard, keyboard, storage, permissions)
print('System tray created successfully!')
print('Check your system tray for the Pasta icon.')
"
              '';
            }

            # Testing Commands
            {
              name = "run-tests";
              category = "testing";
              help = "Run all tests";
              command = ''
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest -xvs
              '';
            }
            {
              name = "test-unit";
              category = "testing";
              help = "Run unit tests only";
              command = ''
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest tests/unit/ -xvs
              '';
            }
            {
              name = "test-integration";
              category = "testing";
              help = "Run integration tests";
              command = ''
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest tests/integration/ -xvs
              '';
            }
            {
              name = "test-gui";
              category = "testing";
              help = "Run GUI tests";
              command = ''
                echo "🖥️ Running GUI tests..."
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest tests/unit/test_*pyside6*.py -xvs
              '';
            }
            {
              name = "test-cov";
              category = "testing";
              help = "Run tests with coverage report";
              command = ''
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest --cov=pasta --cov-report=html --cov-report=term
              '';
            }
            {
              name = "test-watch";
              category = "testing";
              help = "Run tests in watch mode";
              command = ''
                if command -v entr &> /dev/null; then
                  # Unset Qt paths to avoid conflicts with venv PySide6
                  find src tests -name "*.py" | entr -c bash -c "unset QT_PLUGIN_PATH; unset QT_QPA_PLATFORM_PLUGIN_PATH; export QT_QPA_PLATFORM=offscreen; uv run pytest -xvs"
                else
                  echo "Install entr for watch mode (already in shell)"
                fi
              '';
            }

            # Linting and Code Quality
            {
              name = "lint";
              category = "quality";
              help = "Run all linters and checks";
              command = ''
                echo "🎨 Running code quality checks..."
                echo ""
                echo "📝 Ruff check..."
                uv run ruff check .
                echo ""
                echo "🎨 Ruff format check..."
                uv run ruff format --check .
                echo ""
                echo "🔍 Type checking..."
                uv run mypy src/
                echo ""
                echo "✅ All checks passed!"
              '';
            }
            {
              name = "lint-fix";
              category = "quality";
              help = "Fix linting issues automatically";
              command = ''
                echo "🔧 Fixing code issues..."
                uv run ruff check . --fix
                uv run ruff format .
                echo "✅ Code formatted and fixed!"
              '';
            }
            {
              name = "type-check";
              category = "quality";
              help = "Run mypy type checker";
              command = "uv run mypy src/";
            }

            # Documentation
            {
              name = "docs-serve";
              category = "docs";
              help = "Serve documentation locally";
              command = ''
                echo "📚 Serving documentation..."
                cd docs && python -m http.server 8000
              '';
            }
            {
              name = "update-prd";
              category = "docs";
              help = "Check PRD completion status";
              command = ''
                echo "📋 PRD Status:"
                echo ""
                grep -E "^- \[.\]" pasta-prd.md | head -20
                echo ""
                echo "Summary:"
                echo "✅ Completed: $(grep -c "^- \[x\]" pasta-prd.md)"
                echo "⏳ Pending: $(grep -c "^- \[ \]" pasta-prd.md)"
              '';
            }

            # CI/CD Commands
            {
              name = "ci-local";
              category = "ci";
              help = "Run full CI pipeline locally";
              command = ''
                echo "🚀 Running CI pipeline..."
                echo ""
                echo "📦 Checking dependencies..."
                uv sync --frozen
                echo ""
                echo "🎨 Code formatting..."
                uv run ruff format --check .
                echo ""
                echo "📝 Linting..."
                uv run ruff check .
                echo ""
                echo "🔍 Type checking..."
                uv run mypy src/
                echo ""
                echo "🧪 Running tests..."
                # Unset Qt paths to avoid conflicts with venv PySide6
                unset QT_PLUGIN_PATH
                unset QT_QPA_PLATFORM_PLUGIN_PATH
                export QT_QPA_PLATFORM=offscreen
                uv run pytest
                echo ""
                echo "✅ CI pipeline passed!"
              '';
            }
            {
              name = "pre-commit-run";
              category = "ci";
              help = "Run pre-commit hooks on all files";
              command = "uv run pre-commit run --all-files";
            }

            # Utility Commands
            {
              name = "permissions-check";
              category = "utilities";
              help = "Check system permissions for Pasta";
              command = ''
                uv run python -c "
from pasta.utils.permissions import PermissionChecker
checker = PermissionChecker()
print('🔐 Checking permissions...')
if checker.check_permissions():
    print('✅ All permissions OK!')
else:
    print('❌ Missing permissions!')
    checker.request_permissions()
"
              '';
            }
            {
              name = "env-info";
              category = "utilities";
              help = "Show environment information";
              command = ''
                echo "🍝 Pasta Development Environment"
                echo "================================"
                echo ""
                echo "🐍 Python: $(${python}/bin/python3.11 --version)"
                echo "📦 UV: $(uv --version)"
                echo "🎨 Ruff: $(ruff --version)"
                echo ""
                echo "📍 Python path: ${python}/bin/python3.11"
                echo "📍 Project root: $PWD"
                echo ""
                echo "🖥️ GUI Backend: PySide6/Qt6"
                echo "📋 Platform: $(uname -s)"
                echo ""
                echo "🔧 Key dependencies:"
                uv run pip list | grep -E "(pyside6|pyautogui|pyperclip|pystray)" || true
              '';
            }
            {
              name = "todo";
              category = "utilities";
              help = "Find TODO/FIXME comments in code";
              command = ''
                echo "📝 TODO/FIXME/HACK comments:"
                echo ""
                rg -i "TODO|FIXME|HACK" --type py -n || echo "No TODOs found!"
              '';
            }
          ];

          # Startup hook
          devshell.startup = {
            project-setup = {
              text = ''
                # ASCII art logo
                echo "
╔═══════════════════════════════════════╗
║           🍝 PASTA DEV 🍝             ║
║   Cross-platform Clipboard Manager    ║
╚═══════════════════════════════════════╝
"

                # Check project status
                if [ -f "uv.lock" ]; then
                  echo "✅ Project ready! Run 'menu' for commands"
                  echo ""
                  echo "Quick commands:"
                  echo "  • run        - Start the application"
                  echo "  • run-tests  - Run tests"
                  echo "  • lint       - Check code quality"
                  echo "  • dev        - Run with auto-reload"
                else
                  echo "⚠️  No uv.lock found!"
                  echo "Run 'setup' to initialize the project"
                fi
                echo ""
              '';
            };
          };
        };

        # Alternative shell with minimal setup (no devshell menu)
        devShells.minimal = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonWithPackages
            uv
            ruff
          ] ++ buildTools ++ guiDeps ++ platformDeps ++ devTools;

          shellHook = ''
            echo "🍝 Pasta - Minimal Dev Environment"
            echo "Python ${python.version} with UV"
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath (buildTools ++ guiDeps ++ platformDeps)}:$LD_LIBRARY_PATH"
            export UV_SYSTEM_PYTHON=1
            export UV_PYTHON="${python}/bin/python3.11"
            export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt6.qtbase}/lib/qt-6/plugins/platforms"

            # Check if in project
            if [ -f "pyproject.toml" ]; then
              echo "Ready! Use 'uv run python -m pasta' to start"
            fi
          '';
        };

        # Shell specifically for CI/CD environments
        devShells.ci = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonWithPackages
            uv
            ruff
          ] ++ buildTools ++ guiDeps;

          shellHook = ''
            export UV_SYSTEM_PYTHON=1
            export UV_PYTHON="${python}/bin/python3.11"
            export QT_QPA_PLATFORM=offscreen
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
          '';
        };
      });
}
