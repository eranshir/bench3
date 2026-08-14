import json, sys, re

raw = open(sys.argv[1]).read()
resp = json.loads(raw)
text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''

# tolerant: accept 16796, 16,796, \boxed{16796}, ...
target = 16796
passed = False
got = None
for m in re.finditer(r'\d{1,3}(?:,\d{3})*', text):
    if int(m.group(0).replace(',', '')) == target:
        passed = True; got = m.group(0); break
print(json.dumps({'passed': passed, 'expected': target, 'got': got, 'text_tail': text[-500:]}))
