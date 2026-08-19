# Enforcement evidence (matrix, 2026-08-19)

## lunaroute / coding/c1_deadlock / enforced / rep1 — gate fired

Transcript (workspace/.bruno/gate-events.jsonl):

    2026-08-19T18:48:10 revert | deny: implementation mutation before Aegis IR validation (moves 2-4)
      paths: ['__pycache__/hidden_test.cpython-314.pyc']

The agent ran the hidden test before authoring the plan; the mutation (a .pyc cache
artifact) was reverted. The agent then authored the Aegis IR and the git log shows the
full compliant arc: plan (4 children with falsifiers) -> c1..c4 per-child commits ->
closure (Move 5). Resolution: passed, plan_valid=True.

## Other enforced cells (deepseek-flash, gpt-sol, c1 rep1): 0 denies
Models authored conforming IR first (self-compliance under the gate); transcripts
present with gate_start/baseline/allow sequence. The gate's presence enforces the
plan-first ordering even when it never has to revert.

## Singleshot guided caveat
Tool-use tasks (t1-t3) score checker=False in the guided singleshot arm: the aegis
singleshot path does not pass a tools array (the method-comparison prompt is text-only),
so the model cannot emit tool calls. Reported as such; the singleshot guided arm measures
method-compliance artifacts, not the full tool-use benchmark.

## Payload side-effect on singleshot reasoning (2026-08-19)

grok / reasoning/r3_die_expected / guided rep1: the method payload produced a
37,505-char structured response that failed the objective checker (the original
vanilla run passed 3/3). The prose instructions changed the answer FORMAT on a
single-shot reasoning task — a payload-side effect, and the strongest argument
for keeping enforcement claims agentic-only (the method's natural domain).

Other singleshot checker failures are the documented tool-use caveat (t1-t3:
text-only path, no tools array).
