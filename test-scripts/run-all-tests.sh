#!/bin/bash
# Run All Test Scripts
# Executes all numbered test scripts sequentially

set -e

echo "=========================================="
echo "Ansible Sage - Run All Tests"
echo "=========================================="
echo ""

# Create playbooks directory
mkdir -p playbooks

# Find all numbered test scripts
test_scripts=$(ls -1 [0-9][0-9]-*.sh 2>/dev/null | sort)

if [ -z "$test_scripts" ]; then
  echo "❌ No test scripts found!"
  exit 1
fi

total=$(echo "$test_scripts" | wc -l)
current=0
passed=0
failed=0

echo "Found $total test scripts"
echo ""

for script in $test_scripts; do
  current=$((current + 1))
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Running Test $current/$total: $script"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if bash "$script"; then
    passed=$((passed + 1))
    echo "✅ PASSED"
  else
    failed=$((failed + 1))
    echo "❌ FAILED"
  fi

  echo ""
  sleep 2  # Brief pause between tests
done

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total:  $total"
echo "Passed: $passed ✅"
echo "Failed: $failed ❌"
echo ""

if [ $failed -eq 0 ]; then
  echo "🎉 All tests passed!"
  exit 0
else
  echo "⚠️  Some tests failed"
  exit 1
fi
