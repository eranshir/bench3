#!/usr/bin/env python3
"""Re-run check.py over saved single-shot responses and update the CSV.
Used when a checker was fixed after the fact (e.g. LaTeX tolerance).
Zero token cost — responses are already saved in runs/.
"""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH

RUNS = BENCH / 'runs'


def main() -> None:
    csv_path = BENCH / 'results' / 'results_singleshot.csv'
    if not csv_path.exists():
        print('no results_singleshot.csv'); return
    rows = list(csv.DictReader(open(csv_path)))
    fixed = 0
    for r in rows:
        task = r.get('task') or ''
        tdir = BENCH / 'tasks' / task
        if not (tdir / 'check.py').exists():
            continue
        out = RUNS / ('%s_%s_t%s.json' % (r['arm'], task.replace('/', '-'), r['trial']))
        if not out.exists():
            continue
        cp = subprocess.run([sys.executable, str(tdir / 'check.py'), str(out)],
                           capture_output=True, text=True, timeout=120)
        try:
            import json as _json
            score = _json.loads(cp.stdout.strip())
            new_pass = 1 if score.get('passed') else 0
        except Exception:
            new_pass = r.get('passed')
        if str(new_pass) != r.get('passed'):
            r['passed'] = str(new_pass)
            r['tests_failed'] = '0' if new_pass else '1'
            fixed += 1
            print('re-graded %s %s t%s -> pass=%s' % (r['arm'], task, r['trial'], new_pass))
    if fixed:
        with open(csv_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print('updated %d rows' % fixed)
    else:
        print('nothing to regrade')


if __name__ == "__main__":
    main()
