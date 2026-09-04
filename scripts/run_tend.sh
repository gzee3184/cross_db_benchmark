#!/usr/bin/env bash
# End-to-end TEND benchmark evaluation script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

DATA_DIR="${TEND_DATA_DIR:-data/tend}"
MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
OUTPUT_DIR="${OUTPUT_DIR:-results/tend_eval}"
CONCURRENCY="${CONCURRENCY:-8}"

echo "=========================================================================="
echo ">>> RUNNING TEND BENCHMARK EVALUATION"
echo ">>> Data dir:    $DATA_DIR"
echo ">>> Mongo URI:   $MONGO_URI"
echo ">>> Output dir:  $OUTPUT_DIR"
echo "=========================================================================="

python3 -m crossdb.evaluate \
    --backend mongodb \
    --data-dir "$DATA_DIR" \
    --concurrency "$CONCURRENCY" \
    --output-dir "$OUTPUT_DIR"
