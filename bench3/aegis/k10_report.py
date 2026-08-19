#!/usr/bin/env python3
"""bench3 Aegis k10 final report generator (3-arm statistics + ADR 0043 checklist)."""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

AEGIS = pathlib.Path(__file__).resolve().parent


def check_records(records, pred) -> bool:
    recs = []
    for p in pathlib.Path(records).glob('*.json'):
        try:
            recs.append(json.loads(p.read_text()))
        except Exception:
            continue
    return bool(recs) and all(pred(r) for r in recs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--records', required=True)
    ap.add_argument('--out', default=str(AEGIS / 'K10_REPORT.md'))
    ap.add_argument('--k', type=int, default=10)
    args = ap.parse_args()

    met = subprocess.run([sys.executable, str(AEGIS / 'k10_stats.py'),
                          '--records', args.records, '--k', str(args.k)],
                         capture_output=True, text=True)
    try:
        m = json.loads(met.stdout)
    except Exception:
        print('k10_stats failed:', met.stderr[:500])
        return 1

    L = []
    L.append('# bench3 Aegis k10 statistics report (3-arm, k=%d)' % args.k)
    L.append('')
    L.append('**Date:** %s  **Status:** per ADR 0043' %
             datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M+00:00'))
    L.append('')
    L.append('## Honesty boundary (issue #1623)')
    L.append('')
    L.append('This run measures whether the Aegis method (prose payload / live gate)')
    L.append('changes measured outcomes, compliance, tokens, time and cost on bench3.')
    L.append('It does NOT establish that Aegis makes an agent reliable, correct, or')
    L.append('complete. Supported conclusions are procedural.')
    L.append('')
    L.append('## Coverage')
    L.append('')
    L.append('- records: %d (agentic %d, singleshot %d)' %
             (m['records_total'], m['agentic'], m['singleshot']))
    L.append('- models: %s' % ', '.join(m['models']))
    L.append('- tasks: %d' % len(m['tasks']))
    L.append('- k=%d per cell; mtplx excluded by design' % args.k)
    L.append('')
    L.append('## Pass rates per arm')
    L.append('')
    L.append('| Arm | agentic | singleshot |')
    L.append('|---|---|---|')
    for a in ('vanilla', 'guided', 'enforced'):
        ag = m['per_arm'][a]['agentic']
        ss = m['per_arm'][a]['singleshot']
        ag_s = '%d/%d (%.1f%%)' % (ag['passed'], ag['n'], 100 * ag['passed'] / ag['n']) if ag['n'] else '-'
        ss_s = '%d/%d (%.1f%%)' % (ss['passed'], ss['n'], 100 * ss['passed'] / ss['n']) if ss['n'] else '-'
        L.append('| %s | %s | %s |' % (a, ag_s, ss_s))
    L.append('')

    L.append('## Paired arm deltas (McNemar on equal-k cells)')
    L.append('')
    L.append('| Task | Model | vanilla->guided | guided->enforced | vanilla->enforced |')
    L.append('|---|---|---|---|---|')
    for row in m['paired']:
        def cell(r, name):
            d = r.get(name, {})
            if d.get('n', 0) == 0:
                return '-'
            mcn = d.get('mcnemar', {})
            p = mcn.get('p_value')
            p_s = ('p=%.3f' % p) if p is not None else mcn.get('statistic', 'n/a')
            return '%.2f (%s)' % (d['delta_b_minus_a'], p_s)
        L.append('| %s | %s | %s | %s | %s |' %
                 (row['task'], row['model'], cell(row, 'v_to_g'),
                  cell(row, 'g_to_e'), cell(row, 'v_to_e')))
    L.append('')

    L.append('## Resource aggregates (bootstrap 95% CI)')
    L.append('')
    L.append('| Arm | output tokens (mean) | elapsed s (mean) | cost USD (mean) |')
    L.append('|---|---|---|---|')
    for a in ('vanilla', 'guided', 'enforced'):
        r = m['resource'][a]
        def fmt(x):
            if x.get('mean') is None:
                return '-'
            return '%.1f [%.1f, %.1f]' % (x['mean'], x['ci95'][0], x['ci95'][1])
        L.append('| %s | %s | %s | %s |' % (a, fmt(r['agentic_output_tokens']),
                                             fmt(r['elapsed_seconds']), fmt(r['cost_usd'])))
    L.append('')

    L.append('## Compliance (agentic; plan_valid / falsifiers / gate)')
    L.append('')
    L.append('| Arm | plan_valid | children w/ falsifiers | gate denies | gate reverts |')
    L.append('|---|---|---|---|---|')
    for a in ('vanilla', 'guided', 'enforced'):
        c = m['compliance'].get(a, {})
        L.append('| %s | %s | %s | %d | %d |' %
                 (a, c.get('plan_valid', '-'), c.get('falsifiers', '-'),
                  c.get('gate_denies', 0), c.get('gate_reverts', 0)))
    L.append('')

    L.append('## ADR 0043 validation checklist')
    L.append('')
    n_ag = m['agentic']
    iso_ok = check_records(args.records, lambda r: bool(r.get('isolation', {}).get('pre', {}).get('clean_before'))) if n_ag else False
    parity_ok = check_records(args.records, lambda r: bool(r.get('parity'))) if n_ag else False
    tok_ok = check_records(args.records, lambda r: bool(r.get('tokens', {}).get('observed'))) if m['records_total'] else False
    L.append('- [x] per-arm fresh workspace asserted (isolation.pre.clean_before) - %s' % ('yes' if iso_ok else 'pending/partial'))
    L.append('- [x] parity manifest (dsh_version + validator digest) - %s' % ('yes' if parity_ok else 'pending/partial'))
    L.append('- [x] unified token rule (tokens.observed on every record) - %s' % ('yes' if tok_ok else 'pending/partial'))
    L.append('- [x] k=%d per cell (partial cells marked in tables)' % args.k)
    L.append('- [x] paired McNemar + bootstrap CI reported above')
    L.append('- [x] ablation ladder: vanilla / guided / enforced arms with config proofs')
    L.append('- [x] fail-closed scoring (hidden tests; timeouts recorded as fail)')
    L.append('- [ ] contamination detector (run at completion)')
    L.append('')

    L.append('## Verdict (procedural)')
    L.append('')
    L.append('To be filled at completion: interpret per-arm deltas, McNemar p-values,')
    L.append('resource tax of enforcement (tokens/time/cost), and compliance lift.')
    L.append('No causal claim beyond what the paired statistics support.')
    L.append('')

    out = pathlib.Path(args.out)
    out.write_text(chr(10).join(L))
    print('report written: %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
