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

names = [n for n, _ in seq]
checks = {
    'check all three skus': False,
    'reserve all three with qty': False,
    'apply SAVE10 to 150': False,
    'create order for cust-77': False,
    'dependency order': False,
}
skus = set()
for n, a in seq:
    if n == 'check_stock' and 'sku' in a:
        skus.add(a['sku'].upper())
    if n == 'reserve_item':
        ok = a.get('sku', '').upper() in ('A100', 'B200', 'C300') and a.get('qty') and a.get('customer_id') == 'cust-77'
        if not ok:
            pass
    if n == 'apply_discount':
        if abs((a.get('order_total') or 0) - 150.0) < 0.01 and a.get('coupon') == 'SAVE10':
            checks['apply SAVE10 to 150'] = True
    if n == 'create_order':
        if a.get('customer_id') == 'cust-77' and a.get('items'):
            checks['create order for cust-77'] = True
if {'A100', 'B200', 'C300'} <= skus:
    checks['check all three skus'] = True
reserves = [a for n, a in seq if n == 'reserve_item']
if len(reserves) == 3 and all(a.get('qty') and a.get('customer_id') == 'cust-77' for a in reserves):
    checks['reserve all three with qty'] = True
order = names
if all(n in order for n in ('check_stock', 'reserve_item', 'apply_discount', 'create_order')):
    i1 = max(i for i, n in enumerate(order) if n == 'check_stock')
    i2 = max(i for i, n in enumerate(order) if n == 'reserve_item')
    i3 = next(i for i, n in enumerate(order) if n == 'apply_discount')
    i4 = next(i for i, n in enumerate(order) if n == 'create_order')
    if i1 < i2 < i3 < i4:
        checks['dependency order'] = True
npass = sum(checks.values())
print(json.dumps({'passed': npass == len(checks), 'score': npass, 'total': len(checks),
                  'checks': checks, 'sequence': seq}, indent=1))
