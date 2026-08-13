#!/bin/bash
# Drives the full 3-trial matrix sequentially. Sequential on purpose: the runs
# are latency-measured, so overlapping them would contend for local resources
# and muddy the wall-clock numbers.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
for trial in 1 2 3; do
  for model in deepseek gpt; do
    echo "########## $model trial $trial  ($(date '+%H:%M:%S')) ##########"
    "$ROOT/run_bench.sh" "$model" "$trial"
  done
done
echo "########## batch complete $(date '+%H:%M:%S') ##########"
