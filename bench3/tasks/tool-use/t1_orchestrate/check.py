import json, sys

raw = open(sys.argv[1]).read()
resp = json.loads(raw)
calls = (resp.get('choices') or [{}])[0].get('message', {}).get('tool_calls') or []
seq = []
for c in calls:
    fn = c.get('function', {})
    name = fn.get('name', '')
    try:
        args = json.loads(fn.get('arguments') or '{}')
    except Exception:
        args = {}
    seq.append((name, args))

checks = {
    'fetch all three symbols': False,
    'apply fee on subtotal 3000 at 1.5%': False,
    'convert net 2955 USD to EUR at 0.92': False,
    'build invoice for acme-42': False,
    'dependency order respected': False,
}

names = [n for n, _ in seq]
symbols = set()
for n, a in seq:
    if n == 'fetch_quote' and 'symbol' in a:
        symbols.add(a['symbol'].upper())
    if n == 'apply_fee':
        amt = a.get('amount_usd'); fee = a.get('fee_pct')
        if abs((amt or 0) - 3000.0) < 0.01 and abs((fee or 0) - 1.5) < 0.01:
            checks['apply fee on subtotal 3000 at 1.5%'] = True
    if n == 'convert_currency':
        amt = a.get('amount_usd'); to = a.get('to_currency', '').upper(); rate = a.get('rate')
        if abs((amt or 0) - 2955.0) < 0.01 and to == 'EUR' and abs((rate or 0) - 0.92) < 0.01:
            checks['convert net 2955 USD to EUR at 0.92'] = True
    if n == 'build_invoice':
        if a.get('client_id') == 'acme-42' and a.get('lines'):
            checks['build invoice for acme-42'] = True
if {'AAPL', 'MSFT', 'GOOG'} <= symbols:
    checks['fetch all three symbols'] = True

order = [n for n, _ in seq]
if 'fetch_quote' in order and 'apply_fee' in order and 'convert_currency' in order and 'build_invoice' in order:
    i1 = max(i for i, n in enumerate(order) if n == 'fetch_quote')
    i2 = next(i for i, n in enumerate(order) if n == 'apply_fee')
    i3 = next(i for i, n in enumerate(order) if n == 'convert_currency')
    i4 = next(i for i, n in enumerate(order) if n == 'build_invoice')
    if i1 < i2 < i3 < i4:
        checks['dependency order respected'] = True

npass = sum(checks.values())
print(json.dumps({'passed': npass == len(checks), 'score': npass, 'total': len(checks),
                  'checks': checks, 'sequence': seq}, indent=1))
