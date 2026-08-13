#!/bin/bash
# Resumable driver for the hard matrix.
#
# Skips any (model, task, trial) already present in results_hard.csv, so it can
# be re-launched after an interruption without redoing finished work or
# double-counting tokens.
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
RESULTS="$ROOT/results_hard.csv"

done_already() {
    [ -f "$RESULTS" ] || return 1
    grep -q "^$1,$2,$3," "$RESULTS"
}

for trial in 1 2 3; do
  for model in deepseek gpt; do
    for task in $(ls -1 "$ROOT/tasks"); do
      if done_already "$model" "$task" "$trial"; then
        echo "skip $model/$task/t$trial (already recorded)"
        continue
      fi
      echo "########## $model $task trial $trial  ($(date '+%H:%M:%S')) ##########"
      "$ROOT/run_hard.sh" "$model" "$trial" "$task"
    done
  done
done
echo "########## hard batch complete $(date '+%H:%M:%S') ##########"
