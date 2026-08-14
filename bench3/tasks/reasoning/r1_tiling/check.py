import json, sys, re

# reference: tilings of a 3xn board with dominoes
# a(0)=1, a(1)=0, a(2)=3, a(n)=4a(n-2)-a(n-4)
def count(n):
    if n < 0: return 0
    if n == 0: return 1
    if n == 1: return 0
    if n == 2: return 3
    return 4 * count(n - 2) - count(n - 4)

ref = count(30)
raw = open(sys.argv[1]).read()
resp = json.loads(raw)
text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''
m = re.search(r'FINAL ANSWER:\s*([0-9,]+)', text)
got = m.group(1).replace(',', '') if m else None
passed = got is not None and int(got) == ref
print(json.dumps({'passed': passed, 'expected': ref, 'got': got, 'text_tail': text[-600:]}))
