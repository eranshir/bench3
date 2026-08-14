#!/usr/bin/env python3
"""Difficulty ladder: order tasks from hardest down and score how well each
separates the arms.

- difficulty: 1 - overall pass rate (0 = trivial, 1 = nobody solved)
- discrimination: max pairwise pass-rate gap across arms (0..1)
- both: tasks that saturate (all pass or all fail) carry no signal; the
  useful middle is where discrimination is high.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent


def load() -> list:
    rows = []
    for csvf in ('results.csv', 'results_singleshot.csv'):
        p = BENCH / 'results' / csvf
        if p.exists():
            rows.extend(csv.DictReader(open(p)))
    return rows


def main():
    rows = load()
    if not rows:
        print('no results yet'); return
    by_task = defaultdict(list)
    for r in rows:
        by_task[r['task']].append(r)
    ladders = defaultdict(list)
    for task, g in by_task.items():
        rates = {}
        for r in g:
            rates[r['arm']] = rates.get(r['arm'], 0) + int(r['passed'])
        counts = defaultdict(int)
        for r in g:
            counts[r['arm']] += 1
        per_arm = {a: rates.get(a, 0) / counts[a] for a in counts}
        overall = sum(rates.values()) / len(g)
        vals = list(per_arm.values())
        discrimination = max(vals) - min(vals) if vals else 0
        cat = g[0]['category']
        ladders[cat].append({
            'task': task, 'difficulty': round(1 - overall, 2),
            'overall': round(overall, 2), 'discrimination': round(discrimination, 2),
            'per_arm': {k: round(v, 2) for k, v in per_arm.items()},
            'runs': len(g),
        })
    cats = sorted(ladders)
    for c in cats:
        print('\n=== %s ===' % c)
        items = sorted(ladders[c], key=lambda x: -x['difficulty'])
        print('%-24s %-9s %-9s %s' % ('task', 'difficulty', 'discrim', 'per-arm pass'))
        for it in items:
            pa = ' '.join('%s=%s' % (k, v) for k, v in sorted(it['per_arm'].items()))
            print('%-24s %-9s %-9s %s' % (it['task'], it['difficulty'], it['discrimination'], pa))


if __name__ == "__main__":
    main()
