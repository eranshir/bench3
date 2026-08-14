#!/usr/bin/env python3
"""Generate REPORT3.md from the results CSVs, judged scores, and ladder.
Usage: python3 bin/report.py   (writes bench3/REPORT3.md)
"""
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.common import BENCH, load_arms

CATS = ['coding', 'agentic-workflow', 'tool-use', 'reasoning', 'creativity', 'writing']
CAT_LABELS = {'coding': 'Coding', 'agentic-workflow': 'Agentic workflow', 'tool-use': 'Tool use',
              'reasoning': 'Reasoning', 'creativity': 'Creativity', 'writing': 'Writing quality'}


def load_rows():
    rows = []
    for csvf in ('results.csv', 'results_singleshot.csv'):
        p = BENCH / 'results' / csvf
        if p.exists():
            for r in csv.DictReader(open(p)):
                r['cost_usd'] = float(r.get('cost_usd') or 0)
                r['seconds'] = int(r.get('seconds') or 0)
                r['input_tokens'] = int(r.get('input_tokens') or 0)
                r['output_tokens'] = int(r.get('output_tokens') or 0)
                r['reasoning_tokens'] = int(r.get('reasoning_tokens') or 0)
                r['passed'] = int(r.get('passed') or 0)
                rows.append(r)
    return rows


def load_judged():
    p = BENCH / 'results' / 'judged.csv'
    out = {}
    if p.exists():
        for j in csv.DictReader(open(p)):
            out[(j['arm'], j['task'], j['trial'])] = j
    return out


def md_table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |',
             '|' + '---|' * len(headers)]
    for r in rows:
        lines.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    return chr(10).join(lines)


def main():
    rows = load_rows()
    judged = load_judged()
    arms = load_arms()
    arm_order = ['deepseek-flash', 'deepseek-pro', 'gpt-sol', 'grok']
    out = []
    out.append('# DeepSeek / OpenAI / xAI — three-provider benchmark (bench3)')
    out.append('')
    out.append('**Status:** %d runs, $%.4f total spend (list prices).' % (len(rows), sum(r['cost_usd'] for r in rows)))
    out.append('')

    # per-arm totals
    out.append('## Totals')
    out.append('')
    hdr = ['arm', 'runs', 'pass', 'pass %', 'wall s', 'cost $', 'in tok', 'out tok', 'reas tok']
    tbl = []
    for a in arm_order:
        g = [r for r in rows if r['arm'] == a]
        if not g:
            continue
        tbl.append([arms[a]['display'], len(g), sum(r['passed'] for r in g),
                    '%.0f' % (100 * sum(r['passed'] for r in g) / len(g)),
                    sum(r['seconds'] for r in g), '%.4f' % sum(r['cost_usd'] for r in g),
                    sum(r['input_tokens'] for r in g), sum(r['output_tokens'] for r in g),
                    sum(r['reasoning_tokens'] for r in g)])
    out.append(md_table(hdr, tbl))
    out.append('')

    # per-category pass rates
    out.append('## Pass rate by category')
    out.append('')
    hdr = ['category'] + [arms[a]['display'] for a in arm_order]
    tbl = []
    for c in CATS:
        row = [CAT_LABELS.get(c, c)]
        for a in arm_order:
            g = [r for r in rows if r['arm'] == a and r['category'] == c]
            row.append('%d/%d' % (sum(r['passed'] for r in g), len(g)) if g else '—')
        tbl.append(row)
    out.append(md_table(hdr, tbl))
    out.append('')

    # per-task ladder
    out.append('## Difficulty ladder (hardest first)')
    out.append('')
    by_task = defaultdict(list)
    for r in rows:
        by_task[r['task']].append(r)
    ladder = []
    for t, g in by_task.items():
        rates = defaultdict(int)
        counts = defaultdict(int)
        for r in g:
            rates[r['arm']] += r['passed']; counts[r['arm']] += 1
        pa = {a: rates[a] / counts[a] for a in counts}
        overall = sum(rates.values()) / len(g)
        vals = list(pa.values())
        ladder.append((1 - overall, max(vals) - min(vals), t, g[0]['category'], pa))
    ladder.sort(reverse=True)
    hdr = ['task', 'difficulty', 'discrim'] + [arms[a]['display'] for a in arm_order]
    tbl = []
    for diff, disc, t, c, pa in ladder:
        row = [t, '%.2f' % diff, '%.2f' % disc]
        for a in arm_order:
            row.append('%.0f%%' % (100 * pa.get(a, 0)) if a in pa else '—')
        tbl.append(row)
    out.append(md_table(hdr, tbl))
    out.append('')

    # judged quality
    if judged:
        out.append('## Rubric-judged quality (creativity, writing)')
        out.append('')
        hdr = ['task'] + [arms[a]['display'] for a in arm_order]
        tbl = []
        for t in sorted({j['task'] for j in judged.values()}):
            row = [t]
            for a in arm_order:
                means = [float(j['mean']) for k, j in judged.items() if k[0] == a and k[1] == t]
                row.append('%.2f' % statistics.mean(means) if means else '—')
            tbl.append(row)
        out.append(md_table(hdr, tbl))
        out.append('')

    # cost per passing task
    out.append('## Cost per passing task')
    out.append('')
    hdr = ['arm', 'cost/pass $']
    tbl = []
    for a in arm_order:
        g = [r for r in rows if r['arm'] == a]
        npass = sum(r['passed'] for r in g)
        cost = sum(r['cost_usd'] for r in g)
        if npass:
            tbl.append([arms[a]['display'], '%.4f' % (cost / npass)])
    out.append(md_table(hdr, tbl))
    out.append('')

    out.append('_Generated by bin/report.py — raw data in results/, judged.csv, runs/._')
    p = BENCH / 'REPORT3.md'
    p.write_text(chr(10).join(out) + chr(10))
    print('wrote', p)


if __name__ == "__main__":
    main()
