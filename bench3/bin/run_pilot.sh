#!/bin/bash
# Pilot batch: cost-ascending arms, singleshot (3 trials) then agentic (2 trials).
# Resumable: skips cells already in the results CSVs.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/bin"
echo "=== pilot start: $(date) ==="
for arm in deepseek-flash deepseek-pro grok gpt-sol; do
  for trial in 1 2 3; do
    python3 run_singleshot.py "$arm" "$trial" 2>&1 | tail -1 || true
  done
done
echo "=== singleshot done: $(date) ==="
for arm in deepseek-flash deepseek-pro grok gpt-sol; do
  for trial in 1 2; do
    ./run_agentic.sh "$arm" "$trial" 2>&1 | tail -1 || true
  done
done
echo "=== PILOT DONE: $(date) ==="
