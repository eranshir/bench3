#!/usr/bin/env python3
"""Comprehensive results summary: pass rates, medians, cost/pass, judged means.
Usage: python3 bin/summary.py
"""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH, load_arms

ARM_ORDER = ['deepseek-flash', 'deepseek-pro', 'gpt-sol', 'grok', 'mtplx']


def main():
    arms = load_arms()
    rows = []
    for csvf in ('results.csv', 'results_singleshot.csv'):
        p = BENCH / 'results' / csvf
        if p.exists():
            rows.extend(csv.DictReader(open(p)))
    if not rows:
        print('no results'); return

    judged = defaultdict(list)
    jp = BENCH / 'results' / 'judged.csv'
    if jp.exists():
        import json
        for j in csv.DictReader(open(jp)):
            try:
                j['mean'] = float(j.get('mean') or 0)
            except Exception:
                continue
            judged[(j['judge'], j['arm'], j['task'], j['trial'])] = j

    print('=== OVERALL ===')
    for a in ARM_ORDER:
        g = [r for r in rows if r['arm'] == a]
        if not g:
            continue
        npass = sum(int(r['passed']) for r in g)
        cost = sum(float(r['cost_usd']) for r in g)
        secs = sum(int(r['seconds']) for r in g)
        med_s = statistics.median(int(r['seconds']) for r in g)
        print('%s: %d/%d pass (%.0f%%)  cost $%.4f  wall %ds  med %ds' % (
            arms[a]['display'], npass, len(g), 100 * npass / len(g), cost, secs, med_s))

    print()
    print('=== COST PER PASSING TASK ===')
    for a in ARM_ORDER:
        g = [r for r in rows if r['arm'] == a]
        if not g:
            continue
        npass = sum(int(r['passed']) for r in g)
        cost = sum(float(r['cost_usd']) for r in g)
        if npass:
            print('%s: $%.4f per passing task' % (arms[a]['display'], cost / npass))

    print()
    print('=== JUDGED QUALITY (creativity + writing, mean rubric) ===')
    for a in ARM_ORDER:
        means = []
        for (judge, arm, task, trial), j in judged.items():
            if arm == a and judge == 'deepseek-official':
                means.append(j['mean'])
        if means:
            print('%s: %.2f/5 (n=%d)' % (arms[a]['display'], statistics.mean(means), len(means)))

    print()
    print('=== DISCRIMINATING TASKS (discrimination >= 0.5) ===')
    by_task = defaultdict(list)
    for r in rows:
        by_task[r['task']].append(r)
    for t, g in sorted(by_task.items()):
        rates = defaultdict(int)
        counts = defaultdict(int)
        for r in g:
            rates[r['arm']] += int(r['passed']); counts[r['arm']] += 1
        pa = {k: v / counts[k] for k, v in rates.items()}
        vals = list(pa.values())
        disc = max(vals) - min(vals) if vals else 0
        if disc >= 0.5:
            detail = ' '.join('%s=%d%%' % (k, 100 * v) for k, v in sorted(pa.items()))
            print('%s (disc=%.2f): %s' % (t, disc, detail))


if __name__ == "__main__":
    main()
