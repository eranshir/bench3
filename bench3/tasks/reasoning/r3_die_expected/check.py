import json, sys, re, fractions

raw = open(sys.argv[1]).read()
resp = json.loads(raw)
text = (resp.get('choices') or [{}])[0].get('message', {}).get('content') or ''

# tolerant matching: models may write 147/10, 14.7, LaTeX-wrapped
# (\(147/10\), \boxed{\frac{147}{10}=14.7}, 147 / 10, ...)
target = fractions.Fraction(147, 10)
passed = False
got = None
# plain decimals and integers
for m in re.finditer(r'\d+(?:\.\d+)?', text):
    try:
        if fractions.Fraction(m.group(0)) == target:
            passed = True; got = m.group(0); break
    except Exception:
        pass
if not passed:
    # explicit fractions (possibly with spaces/LaTeX around them)
    for m in re.finditer(r'(\d+)\s*/\s*(\d+)', text):
        try:
            if fractions.Fraction(int(m.group(1)), int(m.group(2))) == target:
                passed = True; got = m.group(0); break
        except Exception:
            pass
print(json.dumps({'passed': passed, 'expected': '147/10 = 14.7', 'got': got, 'text_tail': text[-500:]}))
