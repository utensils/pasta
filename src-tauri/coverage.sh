#!/bin/bash

# Run coverage excluding problematic tests
echo "Running code coverage analysis..."

# Export environment variable to exclude clipboard tests
export RUST_TEST_THREADS=1

# Run tarpaulin with safe test subset
cargo tarpaulin \
    --lib \
    --out Html \
    --out Lcov \
    --output-dir ./target/coverage \
    --exclude-files "*/main.rs" \
    --exclude-files "*/build.rs" \
    --exclude-files "*/tests/*" \
    --ignore-panics \
    --skip-clean \
    -- --skip clipboard::tests

echo "Coverage report generated at: target/coverage/tarpaulin-report.html"

# Show coverage summary
if [ -f "target/coverage/lcov.info" ]; then
    echo ""
    echo "Coverage Summary:"
    # Extract coverage percentage from lcov.info
    lines_found=$(grep -E "^DA:" target/coverage/lcov.info | grep -E ",1$" | wc -l | tr -d ' ')
    lines_total=$(grep -E "^DA:" target/coverage/lcov.info | wc -l | tr -d ' ')
    if [ $lines_total -gt 0 ]; then
        coverage_percent=$(echo "scale=2; $lines_found * 100 / $lines_total" | bc)
        echo "Lines covered: $lines_found / $lines_total ($coverage_percent%)"
    fi
fi