#!/bin/bash
# bench3 Mercury worker: all 16 tasks x 3 arms x k=3
LOG="$1"; shift
cd /Users/eranshir/Documents/Projects/deepseek/bench3 || exit 1
export MLXFAST_NO_SANDBOX=1
export LIMIT=900
RECORDS=runs/aegis-mercury-records
mkdir -p "$RECORDS"
{
echo "=== mercury worker started ==="
TASKS="coding/c1_deadlock coding/c2_perf coding/c3_adversarial agentic-workflow/a1_chained agentic-workflow/a2_buildtestfix creativity/k1_product creativity/k2_story reasoning/r1_tiling reasoning/r2_expectedflips reasoning/r3_die_expected reasoning/r4_catalan tool-use/t1_orchestrate tool-use/t2_toolselect tool-use/t3_inventory writing/w1_explain writing/w2_rewrite"
ARMS="vanilla guided enforced"
for task in $TASKS; do
  for arm in $ARMS; do
    for rep in $(seq 1 3); do
      TS=$(echo "$task" | tr '/' '-')
      rec="$RECORDS/$arm"_mercury_"$TS"_rep$rep.json
      [ -f "$rec" ] && { echo "skip (done): mercury $task $arm rep$rep"; continue; }
      if echo "$task" | grep -qE "^(coding|agentic-workflow)/"; then
        RUNNER=aegis_run.py
      else
        RUNNER=aegis_singleshot.py
      fi
      echo "=== RUN: mercury / $task / $arm / rep$rep ==="
      START=$(date +%s)
      python3 "aegis/$RUNNER" --arm "$arm" --model mercury --task "$task" --rep "$rep" --out "$RECORDS" > "$RECORDS/.cell_$$.out" 2>&1
      RC=$?
      END=$(date +%s)
      SECS=$((END - START))
      OUT=$(cat "$RECORDS/.cell_$$.out")
      rm -f "$RECORDS/.cell_$$.out"
      if [ $RC -ne 0 ] && echo "$OUT" | grep -qiE "402 payment|insufficient_quota|quota|billing error|no credits"; then
        echo "  DEPLETED: mercury budget exhausted"
        touch "$RECORDS/.depleted_mercury"
        exit 0
      fi
      if [ $RC -ne 0 ]; then
        echo "  CELL FAILED rc=$RC ($SECS s): $(echo "$OUT" | tail -2 | tr '\n' ' ')"
        continue
      fi
      echo "  done $SECS s"
    done
  done
done
echo "=== mercury worker done ==="
} > "$LOG" 2>&1
