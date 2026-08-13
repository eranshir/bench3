#!/bin/bash
# Runs each benchmark task against one model, in a fresh copy of the fixture.
# Records wall-clock, aggregate tokens, and objective pass/fail from a hidden test.
#
# Usage:
#   ./run_bench.sh deepseek [trial]
#   ./run_bench.sh gpt      [trial]
#   ./run_bench.sh deepseek 2 t3_tdd      # single task, trial 2
#
# Results append to results.csv. Raw stdout per run lands in runs/.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MODEL="${1:?usage: run_bench.sh <deepseek|gpt> [trial] [task]}"
TRIAL="${2:-1}"
ONLY="${3:-}"

case "$MODEL" in
  deepseek) CMD="deepcodex" ;;
  gpt)      CMD="codex" ;;
  *) echo "unknown model '$MODEL' (want: deepseek | gpt)" >&2; exit 2 ;;
esac
command -v "$CMD" >/dev/null || { echo "$CMD not on PATH" >&2; exit 2; }

# Effort matters enormously for both latency and cost, and the two profiles
# default differently (deepseek=high, gpt=xhigh). Pin both to the same value
# for the headline comparison. EFFORT=default uses each profile's own setting.
EFFORT="${EFFORT:-high}"
EFFORT_ARGS=()
[ "$EFFORT" != "default" ] && EFFORT_ARGS=(-c "model_reasoning_effort=\"$EFFORT\"")

RESULTS="$ROOT/results.csv"
mkdir -p "$ROOT/runs" "$ROOT/work"
[ -f "$RESULTS" ] || echo "model,task,trial,effort,seconds,tokens,passed,tests_failed,notes" > "$RESULTS"

TASKS=$(ls -1 "$ROOT/tasks")
[ -n "$ONLY" ] && TASKS="$ONLY"

for task in $TASKS; do
    src="$ROOT/tasks/$task"
    [ -d "$src" ] || { echo "no such task: $task" >&2; continue; }
    work="$ROOT/work/${MODEL}_${task}_t${TRIAL}"
    rm -rf "$work"; cp -R "$src" "$work"
    prompt="$(cat "$work/PROMPT.txt")"
    rm -f "$work/PROMPT.txt"          # the model should not see the file itself
    log="$ROOT/runs/${MODEL}_${task}_t${TRIAL}.log"

    echo "=== $MODEL / $task / trial $TRIAL ==="
    start=$(date +%s)
    ( cd "$work" && "$CMD" "${EFFORT_ARGS[@]}" exec --sandbox workspace-write \
        --skip-git-repo-check "$prompt" < /dev/null ) > "$log" 2>&1
    rc=$?
    end=$(date +%s)
    secs=$((end - start))

    # `codex exec` prints "tokens used" with the count on the FOLLOWING line,
    # as a single aggregate. There is no input/output split available here.
    tokens=$(grep -A1 -i 'tokens used' "$log" | grep -oE '^[0-9,]+$' | tail -1 | tr -d ',')
    tokens="${tokens:-0}"

    notes=""
    if [ $rc -ne 0 ]; then
        notes="cli_exit_$rc"
        grep -qi 'Insufficient Balance' "$log" && notes="insufficient_balance"
        grep -qi 'Unsupported custom tool' "$log" && notes="tool_mode_misconfigured"
        grep -qi '401 Unauthorized' "$log" && notes="auth_expired"
    fi

    # Objective grading: hidden test the model never saw.
    cp "$ROOT/hidden/${task}_test.py" "$work/_hidden_test.py" 2>/dev/null
    gradelog="$ROOT/runs/${MODEL}_${task}_t${TRIAL}.grade"
    ( cd "$work" && python3 -m unittest _hidden_test -v ) > "$gradelog" 2>&1
    grc=$?
    failed=$(grep -cE '^(FAIL|ERROR):' "$gradelog")
    if [ $grc -eq 0 ]; then passed=1; else passed=0; fi

    echo "$MODEL,$task,$TRIAL,$EFFORT,$secs,$tokens,$passed,$failed,$notes" >> "$RESULTS"
    echo "  -> ${secs}s, ${tokens} tokens, passed=$passed, failed_tests=$failed ${notes:+($notes)}"
done

echo
echo "results -> $RESULTS"
