#!/usr/bin/env python3
"""Judge agreement: compare deepseek-v4-pro vs gpt-5.6-sol rubric scores.
Reports per-task mean deltas and per-criterion agreement (exact + within-1).
"""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent


def main():
    p = BENCH / 'results' / 'judged.csv'
    if not p.exists():
        print('no judged.csv yet'); return
    rows = list(csv.DictReader(open(p)))
    by_run = defaultdict(dict)
    for j in rows:
        by_run[(j['arm'], j['task'], j['trial'])][j['judge']] = j

    pairs = [(k, v) for k, v in by_run.items() if 'deepseek-official' in v and 'openai' in v]
    if not pairs:
        print('no runs with both judges yet'); return
    print('runs judged by both: %d' % len(pairs))
    deltas = []
    exact = within1 = total = 0
    for (arm, task, trial), js in pairs:
        a, b = js['deepseek-official'], js['openai']
        sa, sb = eval(a.get('scores') or '{}'), eval(b.get('scores') or '{}')
        d = float(a.get('mean') or 0) - float(b.get('mean') or 0)
        deltas.append(d)
        for k in sa:
            total += 1
            if k in sb:
                if sa[k] == sb[k]:
                    exact += 1
                if abs(sa[k] - sb[k]) <= 1:
                    within1 += 1
    print('mean judge delta (v4pro - gpt): %.2f' % statistics.mean(deltas))
    print('exact agreement: %d/%d (%.0f%%)' % (exact, total, 100 * exact / total))
    print('within-1 agreement: %d/%d (%.0f%%)' % (within1, total, 100 * within1 / total))


if __name__ == "__main__":
    main()
