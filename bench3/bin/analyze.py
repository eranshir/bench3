#!/usr/bin/env python3
"""Summarise bench3 results: pass rates, latency, tokens, cost per arm.
Usage: python3 bin/analyze.py [results.csv ...]
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent


def show(path):
    rows = list(csv.DictReader(open(path)))
    if not rows:
        print(f"{path}: no rows")
        return
    by = defaultdict(list)
    for r in rows:
        by[(r['arm'], r['category'], r['task'])].append(r)

    arms = sorted({r['arm'] for r in rows})
    cats = sorted({r['category'] for r in rows})
    print(f"\n=== {path} ({len(rows)} runs) ===")
    hdr = 'task'.ljust(28) + ''.join(a.rjust(26) for a in arms)
    print(hdr)
    for c in cats:
        tasks = sorted({r['task'] for r in rows if r['category'] == c})
        for t in tasks:
            cells = []
            for a in arms:
                g = [r for r in rows if r['arm'] == a and r['task'] == t]
                if not g:
                    cells.append('-'.rjust(26))
                    continue
                npass = sum(int(r['passed']) for r in g)
                med_s = statistics.median(int(r['seconds']) for r in g)
                cost = sum(float(r['cost_usd']) for r in g)
                tok = sum(int(r['output_tokens']) for r in g)
                cells.append(f"{npass}/{len(g)} {med_s}s ${cost:.3f}".rjust(26))
            print(t.ljust(28) + ''.join(cells))

    print('\nTotals per arm:')
    for a in arms:
        g = [r for r in rows if r['arm'] == a]
        npass = sum(int(r['passed']) for r in g)
        secs = sum(int(r['seconds']) for r in g)
        cost = sum(float(r['cost_usd']) for r in g)
        tok = sum(int(r['input_tokens']) + int(r['output_tokens']) for r in g)
        print(f"  {a}: pass {npass}/{len(g)}  wall {secs}s  cost ${cost:.4f}  tokens {tok:,}")


def main():
    paths = sys.argv[1:] or [str(BENCH / 'results' / p) for p in ('results.csv', 'results_singleshot.csv')]
    for p in paths:
        if Path(p).exists():
            show(p)


if __name__ == "__main__":
    main()
