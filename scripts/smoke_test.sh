#!/usr/bin/env bash
# Fast offline smoke test for crossdb core and backends.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "=========================================================================="
echo ">>> RUNNING CROSSDB SMOKE TESTS"
echo "=========================================================================="

# Run pytest on all test suites
PYTHONPATH=. pytest -v tests/

echo "=========================================================================="
echo ">>> SMOKE TESTS PASSED."
echo "=========================================================================="
