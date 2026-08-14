#!/bin/bash
# Expansion batch: new tasks + extra trials on discriminating tasks.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/bin"
echo "=== expansion start: $(date) ==="

# 1) new single-shot tasks, trials 1-3
for task in reasoning/r3_die_expected reasoning/r4_catalan tool-use/t3_inventory; do
  for trial in 1 2 3; do
    for arm in deepseek-flash deepseek-pro grok gpt-sol; do
      python3 run_singleshot.py "$arm" "$trial" "$task" 2>&1 | tail -1 || true
    done
  done
done

# 2) extra trials (4-5) on the discriminating single-shot tasks
for task in reasoning/r1_tiling tool-use/t1_orchestrate tool-use/t2_toolselect; do
  for trial in 4 5; do
    for arm in deepseek-flash deepseek-pro grok gpt-sol; do
      python3 run_singleshot.py "$arm" "$trial" "$task" 2>&1 | tail -1 || true
    done
  done
done

# 3) new agentic task + one extra a2 trial
for trial in 1 2; do
  ./run_agentic.sh all "$trial" coding/c3_adversarial 2>&1 | tail -1 || true
done
./run_agentic.sh all 3 agentic-workflow/a2_buildtestfix 2>&1 | tail -1 || true

echo "=== EXPANSION DONE: $(date) ==="
