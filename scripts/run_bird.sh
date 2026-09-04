#!/usr/bin/env bash
# End-to-end BIRD benchmark evaluation script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

DATA_DIR="${BIRD_DATA_DIR:-data/bird}"
DB_DIR="${BIRD_DB_DIR:-data/bird/dev_databases}"
OUTPUT_DIR="${OUTPUT_DIR:-results/bird_eval}"
CONCURRENCY="${CONCURRENCY:-8}"
SPLIT="${SPLIT:-all}"

echo "=========================================================================="
echo ">>> RUNNING BIRD BENCHMARK EVALUATION"
echo ">>> Data dir:    $DATA_DIR"
echo ">>> DB dir:      $DB_DIR"
echo ">>> Output dir:  $OUTPUT_DIR"
echo ">>> Split:       $SPLIT"
echo "=========================================================================="

python3 -m crossdb.evaluate \
    --backend sqlite \
    --data-dir "$DATA_DIR" \
    --db-dir "$DB_DIR" \
    --split "$SPLIT" \
    --concurrency "$CONCURRENCY" \
    --output-dir "$OUTPUT_DIR"
