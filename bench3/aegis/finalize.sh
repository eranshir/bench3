#!/bin/bash
# One-shot finalization: run after the matrix completes (all 246 records present).
# Usage: bash aegis/finalize.sh
set -e
cd "$(dirname "$0")/.."
RECS=runs/aegis-records
EXPECTED=246
N=$(ls "$RECS"/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "records: $N (expect $EXPECTED)"
if [ "$N" -lt "$EXPECTED" ]; then
  echo "WARNING: matrix incomplete ($N < $EXPECTED); proceeding with partial data"
fi
echo "== contamination =="
python3 aegis/contamination.py --records "$RECS" 2>&1 | tail -8
echo "== report =="
python3 aegis/aegis_report.py --records "$RECS" --out aegis/REPORT.md
echo "== full metrics sanity =="
python3 aegis/aegis_metrics.py --records "$RECS" > /tmp/metrics-full.json 2>/dev/null && python3 -c "
import json; m=json.load(open('/tmp/metrics-full.json'))
print('arms:', m['arms']); print('models:', m['models'])
print('pass@1:', {a: m['pass_at_1'].get(a) for a in m['arms']})
print('tokens CI:', m.get('tokens_enforced_minus_guided_ci'))
print('validity:', m.get('validity'))
"
echo "== done: aegis/REPORT.md regenerated; review then merge into FINAL_REPORT_DRAFT.md =="
