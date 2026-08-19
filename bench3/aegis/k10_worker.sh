#!/bin/bash
# bench3 Aegis k10 overnight worker: 3 arms x reps 1..10, resumable, anti-hang.
LOG="$1"; shift
cd /Users/eranshir/Documents/Projects/deepseek/bench3 || exit 1
export MLXFAST_NO_SANDBOX=1
export LIMIT=900
RECORDS=runs/aegis-k10-records
mkdir -p "$RECORDS"
{
echo "=== k10 worker started: $* ==="
AGENTIC_TASKS="coding/c1_deadlock coding/c2_perf coding/c3_adversarial agentic-workflow/a1_chained agentic-workflow/a2_buildtestfix"
SS_TASKS="creativity/k1_product creativity/k2_story reasoning/r1_tiling reasoning/r2_expectedflips reasoning/r3_die_expected reasoning/r4_catalan tool-use/t1_orchestrate tool-use/t2_toolselect tool-use/t3_inventory writing/w1_explain writing/w2_rewrite"
ARMS="vanilla guided enforced"

for model in "$@"; do
  DEPLETED=runs/aegis-k10-records/.depleted_$model
  STUCK=runs/aegis-k10-records/.stuck_$model
  rm -f "$STUCK"
  if [ -f "$DEPLETED" ]; then
    echo "SKIP: $model already marked depleted"
    continue
  fi
  for task in $AGENTIC_TASKS $SS_TASKS; do
    for arm in $ARMS; do
      for rep in $(seq 1 10); do
        [ -f "$DEPLETED" ] && { echo "STOP: $model depleted mid-loop"; break 3; }
        [ -f "$STUCK" ] && { echo "STOP: $model stuck (timeout threshold hit)"; break 3; }
        TS=$(echo "$task" | tr '/' '-')
        rec="$RECORDS/$arm"_"$model"_"$TS"_rep$rep.json
        [ -f "$rec" ] && { echo "skip (done): $model $task $arm rep$rep"; continue; }
        if echo "$task" | grep -qE "^(coding|agentic-workflow)/"; then
          TIMEOUT=900; RUNNER=aegis_run.py
        else
          TIMEOUT=420; RUNNER=aegis_singleshot.py
        fi
        echo "=== RUN: $model / $task / $arm / rep$rep (timeout $TIMEOUT s) ==="
        START=$(date +%s)
        python3 "aegis/$RUNNER" --arm "$arm" --model "$model" --task "$task" --rep "$rep" --out "$RECORDS" > "$RECORDS/.cell.out" 2>&1
        RC=$?
        END=$(date +%s)
        SECS=$((END - START))
        OUT=$(cat "$RECORDS/.cell.out")
        rm -f "$RECORDS/.cell.out"
        if echo "$OUT" | grep -qiE "402|insufficient|quota|balance|payment|billing|exhausted"; then
          touch "$DEPLETED"
          echo "  DEPLETED: $model token budget exhausted (rc=$RC) -> stopping model"
          break 3
        fi
        if [ $RC -ne 0 ] && echo "$OUT" | grep -qiE "timeout|timed out|TimedOut"; then
          STRIKES=$(cat "$STUCK" 2>/dev/null || echo 0)
          STRIKES=$((STRIKES + 1))
          echo "$STRIKES" > "$STUCK"
          if [ "$model" = "mtplx" ] || [ "$STRIKES" -ge 2 ]; then
            echo "  STUCK: $model timed out ($STRIKES strikes) -> skipping model"
            break 3
          fi
          echo "  timeout strike $STRIKES for $model, retrying next cell"
          continue
        fi
        if [ $RC -ne 0 ]; then
          echo "  CELL FAILED rc=$RC ($SECS s): $(echo "$OUT" | tail -2 | tr '
' ' ')"
          continue
        fi
        echo "  done $SECS s"
      done
    done
  done
  rm -f "$STUCK"
  echo "=== model complete: $model ==="
done
echo "=== k10 worker done: $* ==="
} > "$LOG" 2>&1
