#!/bin/bash
# Run all health check tests: DB connection, backend, and APIs.
# Usage: ./scripts/run_all_tests.sh [base_url]
# Example: ./scripts/run_all_tests.sh
# Example: ./scripts/run_all_tests.sh http://localhost:8000
# Example: ./scripts/run_all_tests.sh http://your-server:8000

set -e
cd "$(dirname "$0")/.."
BASE_URL="${1:-http://localhost:8000}"

echo "=========================================="
echo "  Recruiter.AI Backend Health Checks"
echo "=========================================="

FAILED=0

echo ""
echo "1. Database connection test..."
if python scripts/test_db.py; then
    :  # pass
else
    FAILED=1
fi

echo ""
echo "2. Backend and API tests (base: $BASE_URL)..."
if python scripts/test_backend.py --base-url "$BASE_URL"; then
    :  # pass
else
    FAILED=1
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "All health checks passed."
    exit 0
else
    echo "One or more health checks failed."
    exit 1
fi
