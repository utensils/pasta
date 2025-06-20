# CI/CD Setup for Pasta

This document describes the continuous integration and deployment setup for the Rust implementation of Pasta.

## GitHub Actions Workflows

### 1. Test Suite (`.github/workflows/test.yml`)
Runs on every push and pull request to ensure code quality:

- **Platforms**: Ubuntu, macOS, Windows
- **Rust versions**: Stable and Beta (beta only on Ubuntu)
- **Checks performed**:
  - Code formatting (`cargo fmt`)
  - Linting (`cargo clippy`)
  - Build verification
  - Unit tests
  - Doc tests
  - Security audit (`cargo audit`)

### 2. Code Coverage (`.github/workflows/coverage.yml`)
Generates code coverage reports:

- **Platform**: Ubuntu (tarpaulin only works on Linux)
- **Coverage tool**: cargo-tarpaulin
- **Reports generated**:
  - XML (Cobertura format) for Codecov
  - HTML for manual review
  - LCOV for additional tools
- **Exclusions**:
  - `main.rs` (entry point)
  - `build.rs` (build script)
  - `clipboard.rs` (can cause segfaults in CI)
  - Test files

## Local Coverage Commands

Run coverage locally using the provided Makefile:

```bash
# Generate coverage report (excluding clipboard tests)
make coverage

# Generate HTML report and open in browser
make coverage-open

# Generate multiple format reports for CI
make coverage-ci

# Clean coverage artifacts
make clean-coverage
```

Or use the shell script:

```bash
./coverage.sh
```

## Codecov Integration

The project is integrated with Codecov for coverage tracking:

- **Configuration**: `codecov.yml` in project root
- **Coverage targets**:
  - Project: 70% (with 5% threshold)
  - Patch: 80% (with 10% threshold)
- **Ignored files**:
  - `main.rs`
  - `build.rs`
  - Test files

## Dependencies

### Linux
The following system dependencies are required:
```bash
sudo apt-get install -y \
  libgtk-3-dev \
  libwebkit2gtk-4.1-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libssl-dev \
  libxdo-dev
```

### macOS
No additional dependencies needed (Xcode Command Line Tools required).

### Windows
No additional dependencies needed (Windows SDK required).

## Running Tests Locally

### Basic test run:
```bash
cargo test
```

### Run tests excluding clipboard tests (recommended for CI):
```bash
cargo test --lib -- --skip clipboard::tests
```

### Run tests with output:
```bash
cargo test -- --nocapture
```

### Run specific test module:
```bash
cargo test config::
```

## Caching Strategy

The CI uses GitHub Actions cache for:
- Cargo registry
- Cargo git dependencies
- Build artifacts (`target/` directory)

This significantly speeds up subsequent CI runs.

## Security

- All workflows run `cargo audit` to check for known vulnerabilities
- Dependencies are automatically scanned by GitHub's Dependabot

## Adding New Tests

When adding new tests:

1. Place unit tests in the same file using `#[cfg(test)]` modules
2. Use `#[serial]` attribute for tests that need exclusive access (e.g., clipboard)
3. Ensure tests work across all platforms or use conditional compilation
4. Aim for at least 70% coverage for new code

## Troubleshooting

### Clipboard tests failing in CI
Clipboard tests are excluded from CI runs as they require display access and can cause segfaults. They should be run locally during development.

### Coverage reports not generating
Ensure tarpaulin is installed:
```bash
cargo install cargo-tarpaulin
```

### Tests timing out
Increase the timeout in `tarpaulin.toml` or use the `--timeout` flag.