#!/bin/bash
# Agentic-only phase: all arms, 2 trials, skips done cells.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/bin"
echo "=== agentic phase: $(date) ==="
for arm in deepseek-flash deepseek-pro grok gpt-sol; do
  for trial in 1 2; do
    ./run_agentic.sh "$arm" "$trial" 2>&1 | tail -1 || true
  done
done
echo "=== AGENTIC DONE: $(date) ==="
