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
    'find account by email': 'find_account_by_email' in names,
    'check failed logins': 'list_failed_logins' in names,
    'unlock': 'unlock_account' in names,
    'notify': 'notify_user' in names,
    'no compliance dump': 'dump_audit_log' not in names,
    'no reset/lock': 'reset_password' not in names and 'lock_account' not in names,
    'no billing/settings/history noise': not ({'get_billing_info','get_account_settings','get_login_history','get_audit_events'} & set(names)),
    'order': False,
}
order = names
if all(n in order for n in ('find_account_by_email', 'list_failed_logins', 'unlock_account', 'notify_user')):
    i1 = next(i for i, n in enumerate(order) if n == 'find_account_by_email')
    i2 = next(i for i, n in enumerate(order) if n == 'list_failed_logins')
    i3 = next(i for i, n in enumerate(order) if n == 'unlock_account')
    i4 = next(i for i, n in enumerate(order) if n == 'notify_user')
    if i1 < i2 < i3 < i4:
        checks['order'] = True
    # account id threading (non-empty, numeric)
    ids = [a.get('account_id') for n, a in seq if n in ('list_failed_logins','unlock_account','notify_user') and a.get('account_id') is not None]
    checks['account id threaded'] = bool(ids) and all(isinstance(i, int) for i in ids)

npass = sum(v for k, v in checks.items() if k != 'account id threaded')
total = sum(1 for k in checks if k != 'account id threaded')
print(json.dumps({'passed': npass == total and checks.get('account id threaded', False),
                  'score': npass, 'total': total, 'checks': checks, 'sequence': seq}, indent=1))
