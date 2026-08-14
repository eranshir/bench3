import json, sys, re

# Catalan number C_10: number of Dyck paths to (10,10) staying below y=x
def catalan(n):
    from math import comb
    return comb(2 * n, n) // (n + 1)

ref = catalan(10)
raw = open(sys.argv[1]).read()
resp = json.loads(raw)
text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''
m = re.search(r'FINAL ANSWER:\s*([0-9,]+)', text)
got = m.group(1).replace(',', '') if m else None
passed = got is not None and int(got) == ref
print(json.dumps({'passed': passed, 'expected': ref, 'got': got, 'text_tail': text[-500:]}))
