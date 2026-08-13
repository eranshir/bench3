#!/bin/bash
# Full hard-suite matrix, sequential (these runs are latency-measured).
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
for trial in 1 2 3; do
  for model in deepseek gpt; do
    echo "########## $model trial $trial  ($(date '+%H:%M:%S')) ##########"
    "$ROOT/run_hard.sh" "$model" "$trial"
  done
done
echo "########## hard batch complete $(date '+%H:%M:%S') ##########"
