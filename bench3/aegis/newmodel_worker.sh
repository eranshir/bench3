#!/bin/bash
# bench3 Aegis new-model worker: glm53-flash / qwen38 x all tasks x 3 arms x k=3
LOG="$1"; TASKSEL="$2"; shift 2
cd /Users/eranshir/Documents/Projects/deepseek/bench3 || exit 1
export MLXFAST_NO_SANDBOX=1
export LIMIT=900
RECORDS=runs/aegis-newmodel-records
mkdir -p "$RECORDS"
{
echo "=== new-model worker started: tasksel=$TASKSEL models=$* ==="
case "$TASKSEL" in
  all)        TASKS="coding/c1_deadlock coding/c2_perf coding/c3_adversarial agentic-workflow/a1_chained agentic-workflow/a2_buildtestfix creativity/k1_product creativity/k2_story reasoning/r1_tiling reasoning/r2_expectedflips reasoning/r3_die_expected reasoning/r4_catalan tool-use/t1_orchestrate tool-use/t2_toolselect tool-use/t3_inventory writing/w1_explain writing/w2_rewrite" ;;
  agentic)    TASKS="coding/c1_deadlock coding/c2_perf coding/c3_adversarial agentic-workflow/a1_chained agentic-workflow/a2_buildtestfix" ;;
  singleshot) TASKS="creativity/k1_product creativity/k2_story reasoning/r1_tiling reasoning/r2_expectedflips reasoning/r3_die_expected reasoning/r4_catalan tool-use/t1_orchestrate tool-use/t2_toolselect tool-use/t3_inventory writing/w1_explain writing/w2_rewrite" ;;
  c1c2)       TASKS="coding/c1_deadlock coding/c2_perf" ;;
  c3a1a2)     TASKS="coding/c3_adversarial agentic-workflow/a1_chained agentic-workflow/a2_buildtestfix" ;;
  ss1)        TASKS="creativity/k1_product creativity/k2_story reasoning/r1_tiling reasoning/r2_expectedflips reasoning/r3_die_expected" ;;
  ss2)        TASKS="reasoning/r4_catalan tool-use/t1_orchestrate tool-use/t2_toolselect tool-use/t3_inventory writing/w1_explain writing/w2_rewrite" ;;
  *) echo "bad tasksel $TASKSEL"; exit 2 ;;
esac
ARMS="vanilla guided enforced"

for model in "$@"; do
  DEPLETED=runs/aegis-newmodel-records/.depleted_$model
  STUCK=runs/aegis-newmodel-records/.stuck_${model}_${TASKSEL}
  rm -f "$STUCK"
  if [ -f "$DEPLETED" ]; then
    echo "SKIP: $model already marked depleted"
    continue
  fi
  for task in $TASKS; do
    for arm in $ARMS; do
      for rep in $(seq 1 3); do
        [ -f "$DEPLETED" ] && { echo "STOP: $model depleted mid-loop"; break 3; }
        if [ -f "$STUCK" ] && [ "$(cat "$STUCK" 2>/dev/null || echo 0)" -ge 4 ]; then { echo "STOP: $model stuck (4+ strikes)"; break 3; }; fi
        TS=$(echo "$task" | tr '/' '-')
        rec="$RECORDS/$arm"_"$model"_"$TS"_rep$rep.json
        [ -f "$rec" ] && { echo "skip (done): $model $task $arm rep$rep"; continue; }
        if echo "$task" | grep -qE "^(coding|agentic-workflow)/"; then
          RUNNER=aegis_run.py
        else
          RUNNER=aegis_singleshot.py
        fi
        echo "=== RUN: $model / $task / $arm / rep$rep ==="
        START=$(date +%s)
        python3 "aegis/$RUNNER" --arm "$arm" --model "$model" --task "$task" --rep "$rep" --out "$RECORDS" > "$RECORDS/.cell_$$.out" 2>&1
        RC=$?
        END=$(date +%s)
        SECS=$((END - START))
        OUT=$(cat "$RECORDS/.cell_$$.out")
        rm -f "$RECORDS/.cell_$$.out"
        if [ $RC -ne 0 ] && echo "$OUT" | grep -qiE "402 payment|insufficient_quota|insufficient balance|quota|payment required|billing error|no credits|out of credits"; then
          touch "$DEPLETED"
          echo "  DEPLETED: $model budget exhausted (rc=$RC)"
          break 3
        fi
        if [ $RC -ne 0 ] && echo "$OUT" | grep -qiE "timeout|timed out|TimedOut"; then
          STRIKES=$(cat "$STUCK" 2>/dev/null || echo 0)
          STRIKES=$((STRIKES + 1))
          echo "$STRIKES" > "$STUCK"
          if [ "$STRIKES" -ge 4 ]; then
            echo "  STUCK: $model timed out ($STRIKES strikes)"
            break 3
          fi
          echo "  timeout strike $STRIKES for $model"
          continue
        fi
        if [ $RC -ne 0 ]; then
          echo "  CELL FAILED rc=$RC ($SECS s): $(echo "$OUT" | tail -2 | tr '\n' ' ')"
          continue
        fi
        echo "  done $SECS s"
      done
    done
  done
  rm -f "$STUCK"
  echo "=== model complete (tasksel=$TASKSEL): $model ==="
done
echo "=== new-model worker done: tasksel=$TASKSEL $* ==="
} > "$LOG" 2>&1
