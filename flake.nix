{
  description = "Pasta - A fast clipboard typing utility built with Rust and Tauri";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    devshell = {
      url = "github:numtide/devshell";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay, devshell }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ 
          (import rust-overlay)
          devshell.overlays.default
        ];
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

        buildDeps = with pkgs; [
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

        # For nix run, we'll use a wrapper that copies files to a writable location
        pasta = pkgs.writeShellScriptBin "pasta" ''
          #!${pkgs.bash}/bin/bash
          
          # Create temporary directory for the app
          TMPDIR=$(mktemp -d)
          trap "rm -rf $TMPDIR" EXIT
          
          # Copy the source to temp directory
          cp -r ${./.}/* $TMPDIR/
          chmod -R +w $TMPDIR
          
          # Set up environment
          export PATH="${rustToolchain}/bin:${pkgs.cargo-tauri}/bin:$PATH"
          export RUST_LOG=''${RUST_LOG:-pasta=info}
          export RUST_BACKTRACE=''${RUST_BACKTRACE:-1}
          
          # Build and run
          cd $TMPDIR
          echo "Building Pasta..."
          cargo build --manifest-path=src-tauri/Cargo.toml --release
          
          echo "Running Pasta..."
          exec ./src-tauri/target/release/pasta
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

        devShells.default = pkgs.devshell.mkShell {
          name = "pasta";
          
          packages = buildDeps ++ (with pkgs; [
            # Tauri CLI
            cargo-tauri
            nodePackages.npm
            
            # Development tools
            # rustfmt, clippy, and rust-analyzer are already included in rustToolchain
            cargo-watch
            cargo-edit
            cargo-outdated
            cargo-audit
            cargo-expand
            cargo-tarpaulin
            
            # Utilities
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

          env = [
            {
              name = "RUST_LOG";
              value = "pasta=info";
            }
            {
              name = "RUST_BACKTRACE";
              value = "1";
            }
            {
              name = "RUST_SRC_PATH";
              value = "${rustToolchain}/lib/rustlib/src/rust/library";
            }
            {
              name = "PKG_CONFIG_PATH";
              value = "${pkgs.openssl.dev}/lib/pkgconfig";
            }
          ];

          devshell.startup = {
            create-dirs = pkgs.lib.stringsWithDeps.noDepEntry ''
              mkdir -p src-tauri/icons
              mkdir -p src-tauri/assets
            '';
            
            platform-message = pkgs.lib.stringsWithDeps.noDepEntry ''
              if [[ "$OSTYPE" == "darwin"* ]]; then
                echo "📱 macOS detected - remember to grant accessibility permissions"
              elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                echo "🐧 Linux detected - X11/Wayland support enabled"
              fi
            '';
          };

          commands = [
              {
                name = "dev";
                help = "Run in development mode with hot reload";
                command = "cargo tauri dev";
                category = "development";
              }
              {
                name = "dev-debug";
                help = "Run in development mode with debug logging";
                command = "RUST_LOG=debug cargo tauri dev";
                category = "development";
              }
              {
                name = "build";
                help = "Build for production";
                command = "cargo tauri build";
                category = "build";
              }
              {
                name = "build-debug";
                help = "Build in debug mode (faster compile, larger binary)";
                command = "cargo build --manifest-path=src-tauri/Cargo.toml";
                category = "build";
              }
              {
                name = "test";
                help = "Run all tests";
                command = "cargo test";
                category = "testing";
              }
              {
                name = "test-lib";
                help = "Run library tests (excludes clipboard tests)";
                command = "cargo test --lib -- --skip clipboard::tests";
                category = "testing";
              }
              {
                name = "test-watch";
                help = "Run tests in watch mode";
                command = "cargo watch -x test";
                category = "testing";
              }
              {
                name = "coverage";
                help = "Generate test coverage report";
                command = "cd src-tauri && ./coverage.sh";
                category = "testing";
              }
              {
                name = "coverage-html";
                help = "Generate and open HTML coverage report";
                command = "cd src-tauri && make coverage-open";
                category = "testing";
              }
              {
                name = "fmt";
                help = "Format code with rustfmt";
                command = "cargo fmt";
                category = "code quality";
              }
              {
                name = "fmt-check";
                help = "Check code formatting";
                command = "cargo fmt --check";
                category = "code quality";
              }
              {
                name = "lint";
                help = "Run clippy linter";
                command = "cargo clippy -- -D warnings";
                category = "code quality";
              }
              {
                name = "lint-fix";
                help = "Run clippy and attempt to fix issues";
                command = "cargo clippy --fix -- -D warnings";
                category = "code quality";
              }
              {
                name = "check";
                help = "Run format check and linter";
                command = "cargo fmt --check && cargo clippy -- -D warnings";
                category = "code quality";
              }
              {
                name = "clean";
                help = "Clean build artifacts";
                command = "cargo clean";
                category = "maintenance";
              }
              {
                name = "clean-all";
                help = "Clean all artifacts including coverage";
                command = "cargo clean && cd src-tauri && make clean-coverage";
                category = "maintenance";
              }
              {
                name = "update";
                help = "Update dependencies";
                command = "cargo update";
                category = "maintenance";
              }
              {
                name = "outdated";
                help = "Check for outdated dependencies";
                command = "cargo outdated";
                category = "maintenance";
              }
              {
                name = "audit";
                help = "Audit dependencies for security vulnerabilities";
                command = "cargo audit";
                category = "maintenance";
              }
              {
                name = "expand";
                help = "Expand macros for debugging";
                command = "cargo expand";
                category = "debugging";
              }
              {
                name = "install-hooks";
                help = "Install git pre-commit hooks";
                command = ''
                  cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
cargo fmt --check
cargo clippy -- -D warnings
EOF
                  chmod +x .git/hooks/pre-commit
                  echo "✅ Git hooks installed!"
                '';
                category = "setup";
              }
              {
                name = "run";
                help = "Build and run the application directly";
                command = "cargo run --manifest-path=src-tauri/Cargo.toml --release";
                category = "development";
              }
              {
                name = "watch";
                help = "Watch for changes and rebuild";
                command = "cargo watch -x 'build --manifest-path=src-tauri/Cargo.toml'";
                category = "development";
              }
            ];

          motd = ''
            {202}🍝 Welcome to Pasta development environment!{reset}
            {italic}A fast clipboard typing utility built with Rust and Tauri{reset}

            {bold}Quick start:{reset}
              {green}dev{reset}      - Run in development mode
              {green}test{reset}     - Run tests
              {green}build{reset}    - Build for production
              {green}menu{reset}     - Show all available commands

            Type {yellow}menu{reset} to see all available commands with descriptions.
          '';
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
      }
    );
}