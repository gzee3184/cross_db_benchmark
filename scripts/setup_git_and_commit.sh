#!/usr/bin/env bash
# Git initialization and commit script for cross_db_benchmark
# Configured specifically for author: gzee3184

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "=========================================================================="
echo ">>> Initializing Git Repository in $ROOT_DIR"
echo "=========================================================================="

# 1. Initialize git repo if not already initialized
if [ ! -d ".git" ]; then
    git init -b main
else
    echo "Git repository already initialized."
fi

# 2. Configure local repository identity to gzee3184
git config user.name "gzee3184"
git config user.email "gazifahimabrar3174@gmail.com"

echo "Configured author identity:"
echo "  user.name:  $(git config user.name)"
echo "  user.email: $(git config user.email)"

# 3. Verify .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "ERROR: .gitignore not found!" >&2
    exit 1
fi

# 4. Stage all non-ignored files
git add .

# 5. Commit as gzee3184
if git diff --cached --quiet; then
    echo "No changes staged for commit."
else
    git commit -m "Initial commit: unified cross-database benchmark suite (SQLite + MongoDB)" \
        --author="gzee3184 <gazifahimabrar3174@gmail.com>"
    echo "Commit created successfully by gzee3184."
fi

# 6. Show commit log
git --no-pager log -n 1

echo "=========================================================================="
echo ">>> To create and push to a new public GitHub repository under gzee3184:"
echo ""
echo "Option A (via GitHub CLI):"
echo "  gh repo create cross_db_benchmark --public --source=. --remote=origin --push"
echo ""
echo "Option B (via standard Git remote):"
echo "  git remote add origin git@github.com:gzee3184/cross_db_benchmark.git"
echo "  git push -u origin main"
echo "=========================================================================="
