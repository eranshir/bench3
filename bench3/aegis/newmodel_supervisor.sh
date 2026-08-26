#!/bin/bash
# Supervises new-model k3 workers (2 models x 4 task-sets).
cd /Users/eranshir/Documents/Projects/deepseek/bench3 || exit 1
WORKER=/tmp/aegis_newmodel_worker.sh
SPECS=(
  "glm53-flash c1c2"  "glm53-flash c3a1a2"  "glm53-flash ss1"  "glm53-flash ss2"
  "qwen38 c1c2"       "qwen38 c3a1a2"       "qwen38 ss1"       "qwen38 ss2"
)
i=0
for spec in "${SPECS[@]}"; do
  set -- $spec
  model=$1; sel=$2
  log=/tmp/newmodel_${model}_${sel}.log
  nohup bash "$WORKER" "$log" "$sel" "$model" > /dev/null 2>&1 &
  disown
  i=$((i+1))
done
echo "supervisor launched $i workers"
wait
echo "=== ALL NEW-MODEL WORKERS COMPLETE ==="
