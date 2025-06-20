{
  description = "Pasta - A fast clipboard typing utility built with Rust and Tauri";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };

        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "rust-analyzer" ];
          targets = [ 
            "x86_64-apple-darwin"
            "aarch64-apple-darwin"
            "x86_64-unknown-linux-gnu"
            "x86_64-pc-windows-gnu"
          ];
        };

        buildInputs = with pkgs; [
          rustToolchain
          pkg-config
          openssl
        ] ++ lib.optionals stdenv.isDarwin [
          darwin.apple_sdk.frameworks.AppKit
          darwin.apple_sdk.frameworks.CoreServices
          darwin.apple_sdk.frameworks.CoreGraphics
          darwin.apple_sdk.frameworks.Foundation
          darwin.apple_sdk.frameworks.WebKit
          libiconv
        ] ++ lib.optionals stdenv.isLinux [
          gtk3
          webkitgtk_4_1
          libayatana-appindicator
          librsvg
          glib
          libsoup_3
        ];

        nativeBuildInputs = with pkgs; [
          cargo-tauri
          nodePackages.npm
          cargo-tarpaulin
        ];

        pasta = pkgs.rustPlatform.buildRustPackage rec {
          pname = "pasta";
          version = "0.1.0";
          
          src = ./.;
          
          cargoLock = {
            lockFile = ./src-tauri/Cargo.lock;
          };

          cargoBuildFlags = [ "--manifest-path=src-tauri/Cargo.toml" ];
          
          buildInputs = buildInputs;
          nativeBuildInputs = nativeBuildInputs ++ [ pkgs.makeWrapper ];

          buildPhase = ''
            runHook preBuild
            
            cd src-tauri
            cargo build --release
            
            runHook postBuild
          '';

          installPhase = ''
            runHook preInstall
            
            mkdir -p $out/bin
            cp target/release/pasta-rust $out/bin/pasta
            
            runHook postInstall
          '';

          meta = with pkgs.lib; {
            description = "A fast clipboard typing utility";
            homepage = "https://github.com/yourusername/pasta";
            license = licenses.mit;
            maintainers = with maintainers; [ ];
            platforms = platforms.all;
          };
        };

        devMenuScript = pkgs.writeShellScriptBin "menu" ''
          ${pkgs.gum}/bin/gum style \
            --foreground 212 --border-foreground 212 --border double \
            --align center --width 50 --margin "1 2" --padding "1 2" \
            "Pasta Development Menu"
          
          CMD=$(${pkgs.gum}/bin/gum choose \
            "Run in development mode" \
            "Run with debug logging" \
            "Build for production" \
            "Run tests" \
            "Run linter (clippy)" \
            "Format code" \
            "Generate coverage report" \
            "Open coverage in browser" \
            "Clean build artifacts" \
            "Install git hooks" \
            "Exit")
          
          case "$CMD" in
            "Run in development mode")
              echo "Starting Pasta in development mode..."
              cargo tauri dev
              ;;
            "Run with debug logging")
              echo "Starting Pasta with debug logging..."
              RUST_LOG=debug cargo tauri dev
              ;;
            "Build for production")
              echo "Building Pasta for production..."
              cargo tauri build
              ;;
            "Run tests")
              echo "Running tests..."
              cargo test --lib -- config:: window::
              ;;
            "Run linter (clippy)")
              echo "Running clippy..."
              cargo clippy -- -D warnings
              ;;
            "Format code")
              echo "Formatting code..."
              cargo fmt
              ;;
            "Generate coverage report")
              echo "Generating coverage report..."
              ./coverage.sh
              ;;
            "Open coverage in browser")
              echo "Opening coverage report..."
              make coverage-open
              ;;
            "Clean build artifacts")
              echo "Cleaning build artifacts..."
              cargo clean
              make clean-coverage
              ;;
            "Install git hooks")
              echo "Installing git hooks..."
              cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
cargo fmt --check
cargo clippy -- -D warnings
EOF
              chmod +x .git/hooks/pre-commit
              echo "Git hooks installed!"
              ;;
            "Exit")
              echo "Goodbye!"
              exit 0
              ;;
          esac
        '';

      in
      {
        packages = {
          default = pasta;
          pasta = pasta;
        };

        apps = {
          default = flake-utils.lib.mkApp {
            drv = pasta;
            name = "pasta";
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = buildInputs ++ nativeBuildInputs ++ (with pkgs; [
            # Development tools
            rustfmt
            clippy
            rust-analyzer
            cargo-watch
            cargo-edit
            cargo-outdated
            cargo-audit
            cargo-expand
            
            # Utilities
            gum
            jq
            ripgrep
            fd
            bat
            git
            gnumake
            
            # Platform-specific dev tools
          ] ++ lib.optionals stdenv.isLinux [
            xorg.libX11
            xorg.libXcursor
            xorg.libXrandr
            xorg.libXi
            xorg.libxcb
          ]);

          shellHook = ''
            echo "🍝 Welcome to Pasta development environment!"
            echo ""
            echo "Available commands:"
            echo "  menu              - Interactive development menu"
            echo "  cargo tauri dev   - Run in development mode"
            echo "  cargo tauri build - Build for production"
            echo "  cargo test        - Run tests"
            echo "  cargo fmt         - Format code"
            echo "  cargo clippy      - Run linter"
            echo ""
            echo "Quick actions:"
            echo "  nix run           - Run the application"
            echo "  nix build         - Build the application"
            echo ""
            
            # Set up environment variables
            export RUST_LOG=pasta_rust=info
            export RUST_BACKTRACE=1
            
            # Create necessary directories
            mkdir -p src-tauri/icons
            mkdir -p src-tauri/assets
            
            # Platform-specific setup
            if [[ "$OSTYPE" == "darwin"* ]]; then
              echo "📱 macOS detected - remember to grant accessibility permissions"
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
              echo "🐧 Linux detected - X11/Wayland support enabled"
            fi
            
            echo ""
            echo "Type 'menu' to access the interactive development menu"
          '';

          # Environment variables
          RUST_SRC_PATH = "${rustToolchain}/lib/rustlib/src/rust/library";
          PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
        };

        # Additional development shells for specific tasks
        devShells.ci = pkgs.mkShell {
          buildInputs = [ rustToolchain pkgs.cargo-tarpaulin ];
          shellHook = ''
            echo "CI environment ready"
          '';
        };

        devShells.minimal = pkgs.mkShell {
          buildInputs = [ rustToolchain ];
          shellHook = ''
            echo "Minimal Rust environment ready"
          '';
        };

        # Packages available in the flake
        packages.devMenu = devMenuScript;
      }
    );
}