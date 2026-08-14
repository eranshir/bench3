import json, sys, re, fractions

raw = open(sys.argv[1]).read()
resp = json.loads(raw)
text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''
m = re.search(r'FINAL ANSWER:\s*([0-9]+(?:\s*[/.]\s*[0-9]+)?)', text)
got = m.group(1).replace(' ', '') if m else None
passed = False
if got:
    try:
        passed = fractions.Fraction(got) == fractions.Fraction(147, 10)
    except Exception:
        passed = False
print(json.dumps({'passed': passed, 'expected': '147/10 = 14.7', 'got': got, 'text_tail': text[-500:]}))
