# P0-P2 validation note (2026-08-19)

Canary + end-to-end smokes on deepseek-flash / coding/c3_adversarial:

1. Gate validator: deny with no IR (rc=1); allow with plan+children+falsifiers (rc=0). ✓
2. Gate daemon canary: pre-plan write REVERTED + logged; post-plan write persists. ✓
3. Guided arm end-to-end: passed; authored .bruno/ children with falsifiers. With the
   explicit IR schema in the payload, the model authored a FULLY CONFORMING plan
   (plan_valid=True, 2 children, falsifiers [3,3]). ✓
4. Enforced arm end-to-end (gate ON): passed (417s), plan_valid=True, 3 children
   [2,1,3 falsifiers], gate transcript present (0 denies — the agent complied first).
   git log shows the full Five-Move arc: plan → children → falsifier f3 FIRED and the
   greedy approach was retracted → per-child commits → closure recorded. ✓

The enforcement mechanism is proven live (canary) and the enforced arm produces a
method-compliant trajectory with a materialization-proof transcript.
