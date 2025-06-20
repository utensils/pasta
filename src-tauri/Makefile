.PHONY: test coverage coverage-html coverage-open clean-coverage

# Run all tests
test:
	cargo test

# Run tests with coverage (excluding non-testable Tauri modules)
coverage:
	cargo tarpaulin --config tarpaulin.toml --skip-clean --ignore-tests

# Generate HTML coverage report
coverage-html:
	cargo tarpaulin --config tarpaulin.toml --skip-clean --out Html

# Generate coverage and open in browser
coverage-open: coverage-html
	open target/coverage/tarpaulin-report.html || xdg-open target/coverage/tarpaulin-report.html || start target/coverage/tarpaulin-report.html

# Run full coverage including all tests (may fail on some systems)
coverage-full:
	cargo tarpaulin --config tarpaulin.toml --skip-clean

# Clean coverage artifacts
clean-coverage:
	rm -rf target/coverage/
	rm -f cobertura.xml tarpaulin-report.html lcov.info
	find . -name "*.profraw" -delete
	find . -name "*.profdata" -delete

# Install coverage tools
install-coverage:
	cargo install cargo-tarpaulin

# Run coverage and generate multiple format reports
coverage-ci:
	cargo tarpaulin --config tarpaulin.toml --skip-clean --out Xml --out Lcov --out Html