#!/bin/bash
# Hard-suite runner. Same contract as ../run_bench.sh, with two differences:
#   - a per-run watchdog, because these tasks can genuinely take minutes and a
#     wedged CLI would otherwise stall the whole batch
#   - grading can be slow (h2 spends up to 45s per hung concurrency scenario),
#     so grade wall-clock is recorded separately from model wall-clock
#
# Usage:
#   ./run_hard.sh deepseek [trial] [task]
#   ./run_hard.sh gpt      [trial] [task]
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MODEL="${1:?usage: run_hard.sh <deepseek|gpt> [trial] [task]}"
TRIAL="${2:-1}"
ONLY="${3:-}"

case "$MODEL" in
  deepseek) CMD="deepcodex" ;;
  gpt)      CMD="codex" ;;
  *) echo "unknown model '$MODEL' (want: deepseek | gpt)" >&2; exit 2 ;;
esac
command -v "$CMD" >/dev/null || { echo "$CMD not on PATH" >&2; exit 2; }

EFFORT="${EFFORT:-high}"
EFFORT_ARGS=()
[ "$EFFORT" != "default" ] && EFFORT_ARGS=(-c "model_reasoning_effort=\"$EFFORT\"")

# per-run wall-clock ceiling for the agent itself, seconds
LIMIT="${LIMIT:-900}"

RESULTS="$ROOT/results_hard.csv"
mkdir -p "$ROOT/runs" "$ROOT/work"
[ -f "$RESULTS" ] || echo "model,task,trial,effort,seconds,grade_seconds,tokens,passed,tests_failed,notes" > "$RESULTS"

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
        --skip-git-repo-check "$prompt" < /dev/null ) > "$log" 2>&1 &
    agent=$!
    ( sleep "$LIMIT"; kill -9 "$agent" 2>/dev/null ) > /dev/null 2>&1 &
    watchdog=$!
    wait "$agent"; rc=$?
    kill "$watchdog" 2>/dev/null; wait "$watchdog" 2>/dev/null
    end=$(date +%s)
    secs=$((end - start))

    tokens=$(grep -A1 -i 'tokens used' "$log" | grep -oE '^[0-9,]+$' | tail -1 | tr -d ',')
    tokens="${tokens:-0}"

    notes=""
    if [ $rc -ne 0 ]; then
        notes="cli_exit_$rc"
        [ $secs -ge $LIMIT ] && notes="timeout_${LIMIT}s"
        grep -qi 'Insufficient Balance' "$log" && notes="insufficient_balance"
        grep -qi 'Unsupported custom tool' "$log" && notes="tool_mode_misconfigured"
        grep -qi '401 Unauthorized' "$log" && notes="auth_expired"
    fi

    # Objective grading: hidden test the model never saw.
    cp "$ROOT/hidden/${task}_test.py" "$work/_hidden_test.py" 2>/dev/null
    gradelog="$ROOT/runs/${MODEL}_${task}_t${TRIAL}.grade"
    gstart=$(date +%s)
    ( cd "$work" && python3 -m unittest _hidden_test -v ) > "$gradelog" 2>&1
    grc=$?
    gsecs=$(( $(date +%s) - gstart ))
    failed=$(grep -cE '^(FAIL|ERROR):' "$gradelog")
    if [ $grc -eq 0 ]; then passed=1; else passed=0; fi

    echo "$MODEL,$task,$TRIAL,$EFFORT,$secs,$gsecs,$tokens,$passed,$failed,$notes" >> "$RESULTS"
    echo "  -> ${secs}s agent, ${gsecs}s grade, ${tokens} tokens, passed=$passed, failed_tests=$failed ${notes:+($notes)}"
done

echo
echo "results -> $RESULTS"
