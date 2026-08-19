# ADR 0043 validation checklist — Aegis k10 statistics run

Checklist items are assessed at completion against the full k10 records
(runs/aegis-k10-records). Marked [x] only when the evidence is present.

## Rule 1 — Arm isolation / contamination
- [ ] per-arm fresh workspace asserted (isolation.pre.clean_before = True on every agentic record)
- [ ] contamination detector run; directional leakage symmetric / below threshold
- [ ] vanilla control_absent_by_config = True (payload proven absent, not just unmeasured)

## Rule 2 — Materialization proof
- [ ] every agentic record carries payload_digest (guided/enforced) or control_absent (vanilla)
- [ ] enforced arm carries gate_transcript (denies/reverts/allows) — the live-gate proof

## Rule 3 — Parity manifest (pinned tooling)
- [ ] dsh_version identical across all records (one binary)
- [ ] one gate_validator_digest (bench3-pinned; divergence from aegis release binary recorded)
- [ ] one model per arm; provider recorded

## Rule 4 — Unified token rule
- [ ] tokens.observed=True on every record (agentic + singleshot)
- [ ] resource aggregates use the same token buckets across arms

## Rule 5 — Statistical floor
- [ ] k=10 per (task, model, arm) cell (or partial marked as such)
- [ ] paired McNemar on vanilla->guided and guided->enforced (equal-k cells)
- [ ] bootstrap 95% CI on tokens / time / cost deltas
- [ ] no causal phrasing where CI includes 0

## Rule 6 — Ablation ladder
- [ ] arms present with config proofs: vanilla (rung 1), guided/prose (rung 3), enforced/gates (rung 4)
- [ ] identical instructions across guided/enforced; only gate liveness differs

## Rule 7 — Fail-closed scoring
- [ ] hidden-test grading; unresolved/timeout recorded as fail
- [ ] scoring fail-closed: no partial credit where tests did not run

## Honesty boundary (issue #1623)
- [ ] report frames conclusions as procedural; no claim that Aegis makes agents reliable
- [ ] children #1629/#1630/#1636 semantics noted (trail_valid rubric, per-unit adherence, closure contract)
