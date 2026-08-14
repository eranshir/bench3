#!/bin/bash
# Agentic-mode runner: every category that needs a real agent loop
# (coding, agentic-workflow) runs through the DSH headless harness with an
# isolated DSH_HOME so the benchmark never touches the user's GUI settings.
#
# Usage:
#   ./run_agentic.sh                      # all arms, all tasks, trial 1
#   ./run_agentic.sh gpt-sol              # one arm, all tasks, trial 1
#   ./run_agentic.sh gpt-sol 2 coding/c1  # one arm, one task, trial 2
#
# Env: LIMIT (per-run watchdog seconds, default 900)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="python3"
export PYTHONPATH="$ROOT/bin${PYTHONPATH:+:$PYTHONPATH}"

ARM="${1:-all}"
TRIAL="${2:-1}"
ONLY="${3:-}"

DSH_HOME="$ROOT/.dsh-home"
WORK="$ROOT/work"
RUNS="$ROOT/runs"
RESULTS="$ROOT/results/results.csv"
mkdir -p "$WORK" "$RUNS" "$(dirname "$RESULTS")"
[ -f "$RESULTS" ] || echo "arm,vendor,model,category,task,trial,effort,mode,seconds,input_tokens,cache_read_tokens,output_tokens,reasoning_tokens,cost_usd,passed,tests_failed,grade_seconds,notes,session_path,log_path" > "$RESULTS"

# resolve arm list
if [ "$ARM" = "all" ]; then
  ARMS=$($PY -c "import sys; sys.path.insert(0,'$ROOT/bin'); from lib.common import load_arms; print(' '.join(load_arms().keys()))")
else
  ARMS="$ARM"
fi

# resolve task list
if [ -n "$ONLY" ]; then
  TASKS="$ONLY"
else
  TASKS=$($PY - <<'EOF'
import sys
sys.path.insert(0, '/Users/eranshir/Documents/Projects/deepseek/bench3/bin')
from pathlib import Path
root = Path('/Users/eranshir/Documents/Projects/deepseek/bench3/tasks')
out = []
for cat in sorted(root.iterdir()):
    if not cat.is_dir(): continue
    for t in sorted((root/cat).iterdir()):
        if (t/'PROMPT.txt').exists():
            out.append(f"{cat.name}/{t.name}")
print(' '.join(out))
EOF
)
fi

# credentials from the user's real store, exported for the isolated home (env wins)
eval "$($PY - <<'EOF'
import sys
sys.path.insert(0, '/Users/eranshir/Documents/Projects/deepseek/bench3/bin')
from lib.common import load_credentials
for k, v in load_credentials().items():
    print(f'export {k}={v!r}')
EOF
)"

for arm in $ARMS; do
  read -r APROV AMODEL AEFFORT <<< "$($PY -c "
import sys; sys.path.insert(0,'$ROOT/bin')
from lib.common import load_arms
a = load_arms()['$arm']
print(a['provider'], a['model'], a['effort'])
")"
  # pin this arm in the isolated home settings (effort included)
  $PY "$ROOT/bin/lib/write_settings.py" "$APROV" "$AMODEL" "$AEFFORT"

  for task in $TASKS; do
    catname="${task%%/*}"; tname="${task##*/}"
    src="$ROOT/tasks/$task"
    [ -d "$src" ] || { echo "no such task: $task" >&2; continue; }
    # resume: skip already-recorded cells
    if grep -q "^$arm,[^,]*,[^,]*,$catname,$tname,$TRIAL," "$RESULTS" 2>/dev/null; then
      echo "skip (done): $arm $task t$TRIAL"; continue
    fi
    work="$WORK/${arm}_${catname}-${tname}_t${TRIAL}"
    rm -rf "$work"; cp -R "$src" "$work"
    prompt="$(cat "$work/PROMPT.txt")"
    rm -f "$work/PROMPT.txt"
    # workspace key for session lookup: --<realpath with / -> ->--
    workkey="--$(cd "$work" && pwd -P | sed 's|^/||; s|/|-|g')--"

    echo "=== $arm / $task / trial $TRIAL ==="
    log="$RUNS/${arm}_${catname}-${tname}_t${TRIAL}.log"
    start=$(date +%s)
    ( cd "$work" && DSH_HOME="$DSH_HOME" dsh --profile headless "$prompt" ) > "$log" 2>&1 &
    agent=$!
    ( sleep "${LIMIT:-900}"; kill -9 "$agent" 2>/dev/null ) >/dev/null 2>&1 &
    watchdog=$!
    wait "$agent"; rc=$?
    kill "$watchdog" 2>/dev/null; wait "$watchdog" 2>/dev/null
    end=$(date +%s)
    secs=$((end - start))

    notes=""
    [ $rc -ne 0 ] && notes="cli_exit_$rc"
    [ $secs -ge "${LIMIT:-900}" ] && notes="timeout_${LIMIT}s"

    # usage from the newest session under this workspace key. dsh flushes
    # the session asynchronously (worker teardown), so poll for it.
    sess=$($PY -c "
import sys
sys.path.insert(0, '$ROOT/bin')
from pathlib import Path
from lib.session import wait_session
p = wait_session('$workkey', Path('$DSH_HOME'), $start, timeout=120)
print(p or '')
")
    if [ -n "$sess" ]; then
      usage=$($PY -c "
import sys, json
sys.path.insert(0, '$ROOT/bin')
from lib.session import parse_session
r = parse_session('$sess')
print(json.dumps(r['usage']))
")
      IN_TOK=$(echo "$usage" | $PY -c "import sys,json; print(json.load(sys.stdin)['input'])")
      CA_TOK=$(echo "$usage" | $PY -c "import sys,json; print(json.load(sys.stdin)['cached'])")
      OUT_TOK=$(echo "$usage" | $PY -c "import sys,json; print(json.load(sys.stdin)['output'])")
      RE_TOK=$(echo "$usage" | $PY -c "import sys,json; print(json.load(sys.stdin)['reasoning'])")
    else
      IN_TOK=0; CA_TOK=0; OUT_TOK=0; RE_TOK=0
      [ -z "$notes" ] && notes="no_session"
    fi
    COST=$($PY -c "
import sys
sys.path.insert(0, '$ROOT/bin')
from lib.common import load_arms, cost_usd
a = load_arms()['$arm']
print(f'{cost_usd(a, $IN_TOK, $CA_TOK, $OUT_TOK):.6f}')
")

    # objective grading: hidden test the model never saw
    passed=0; failed=0; gsecs=0
    if [ -f "$ROOT/tasks/$task/hidden_test.py" ]; then
      cp "$ROOT/tasks/$task/hidden_test.py" "$work/_hidden_test.py"
      glog="$RUNS/${arm}_${catname}-${tname}_t${TRIAL}.grade"
      gstart=$(date +%s)
      ( cd "$work" && python3 -m unittest _hidden_test -v ) > "$glog" 2>&1
      grc=$?
      gsecs=$(( $(date +%s) - gstart ))
      failed=$(grep -cE '^(FAIL|ERROR):' "$glog")
      [ $grc -eq 0 ] && passed=1
    fi

    echo "$arm,$(echo "$arm" | sed 's/-.*//'),$AMODEL,$catname,$tname,$TRIAL,$AEFFORT,agentic,$secs,$IN_TOK,$CA_TOK,$OUT_TOK,$RE_TOK,$COST,$passed,$failed,$gsecs,$notes,$sess,$log" >> "$RESULTS"
    echo "  -> ${secs}s, in=$IN_TOK cached=$CA_TOK out=$OUT_TOK reas=$RE_TOK cost=\$$COST passed=$passed failed=$failed ${notes:+($notes)}"
  done
done
echo
echo "results -> $RESULTS"
