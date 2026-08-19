# bench3 Aegis guided-vs-enforced — Pre-Registration

**Status:** FROZEN (pre-data) · **Date:** 2026-08-19 · **Freeze commit:** filled at implementation start
**Authority:** ADR 0043 (mithran-hq/aegis) — a run is quotable only when every condition holds, harness-enforced.
**Honesty boundary (issue #1623):** this run measures whether **live enforcement** of the Aegis method
changes measured adherence and outcomes on bench3 tasks vs prose guidance alone. It does NOT establish that
Aegis makes an agent reliable, correct, or complete. The supported conclusion is procedural.

## Arms (Rule 6 ladder — the two rungs this run exists to compare)

| Arm | Method text | Gate | Config proof |
|---|---|---|---|
| aegis-guided | yes (payload P1) | off | payload digest read from session |
| aegis-enforced | yes (identical P1) | ON (workspace-resident gate) | gate transcript + canary verdict |
| vanilla (control, optional) | absent by explicit config | off | AEGIS_BENCH_CONTROL_ARM=1 |

Identical instructions across guided/enforced; the ONLY difference is whether the gate is live.

## Cohort

- **Agentic tasks (5):** coding c1_deadlock, c2_perf, c3_adversarial; agentic-workflow a1_chained, a2_buildtestfix.
- **Singleshot tasks (11):** reasoning r1–r4, tool-use t1–t3, creativity k1–k2, writing w1–w2.
- **Models:** all bench3 arms (deepseek-flash, deepseek-pro, gpt-sol, grok, mtplx, lunaroute).
- **Repetitions:** k = 3 per (task × arm). MTPLX agentic is the long pole; staged execution (cloud first, MTPLX last), resumable.

## Enforcement contract (gate)

Workspace-resident gate (bench3/aegis/gate_daemon.py + validator), the DSH-adapter analogue of the codex
PreToolUse gate:

1. The agent may mutate implementation files ONLY after the workspace Aegis IR validates:
   .bruno/plan.json (with assumption ledger) + .bruno/children/*.json, each child with
   id/scope/acceptance/falsifiers[id, description, check{command, expected_outcome}]/status.
2. Pre-validation mutations are REVERTED by the gate daemon; a git pre-commit hook refuses commits without
   valid IR. The agent observes its unvalidated work disappear and a denial reason.
3. Every decision is appended to <workspace>/.bruno/gate-events.jsonl (the materialization-proof transcript).
4. Gate modes: strict (default). Soft is a pilot-only calibration, never reported as the enforced arm.
5. Canary (before data): a pre-plan Write must be reverted and logged — proves the gate is live, not decorative.

## Singleshot treatment

- aegis-guided: method instructions injected into the request system prompt.
- aegis-enforced: same instructions + harness-side response gate — the run FAILS (unresolved) if the
  response does not carry the method artifacts (plan, falsifiers, closure). Documented as the weakest rung;
  if it proves brittle, singleshot is reported guided-only and enforcement claims are restricted to agentic.

## Metrics (mirrors K10 + smoke5)

- Resolution (hidden tests, fail-closed; timeout = unresolved).
- Compliance vector: plan_present_before_first_mutation; per-child falsifier count + validity;
  closure attempted/reconciled; trail_valid (ONE rubric, per #1629; per-artifact not per-turn, per #1630).
- pass@1 mean; pass^k (resolved in all k — determinism claim); false-done (final claim vs verified);
  tokens/resolved; wasted-token fraction; enforcement-lift = enforced − guided per task.
- Paired per-task statistics: McNemar on resolution; bootstrap 95% CIs on continuous deltas.
  No causal phrasing where CI includes 0.

## Decision rule (falsifiable)

- D1 — Enforcement changes trajectory: TRUE iff the enforced compliance vector (plan-before-mutation,
  falsifiers, closure) has a 95% CI excluding the guided vector on ≥1 agentic task, or enforced pass^k
  differs from guided pass^k on ≥1 task with CI excluding 0.
- D2 — Enforcement costs tokens: enforced vs guided tokens-per-resolved-task delta reported either way.
- D3 — Correctness-neutrality: enforced−guided resolution delta reported either way; enforcement is NOT
  assumed correctness-neutral.

Any null is the reported result. No cell dropped after the fact; any validity failure ⇒ void protocol.

## Validity checklist (ADR 0043 → bench3)

1. Arm isolation: fresh workspace per (arm × rep); fail-closed clean git + HEAD==base; contamination
   detector on output patches (threshold 0.20); cohort manifest committed.
2. Materialization proof: payload digest (guided) / gate transcript + canary (enforced) / proven absence (control).
3. Parity manifest: one pinned DSH + one model per arm, real versions per task; gate validator pinned
   (digest recorded; does not match the aegis product release — recorded divergence, Rule 3).
4. Unified token rule: identical accounting both arms; aux buckets named (gate: deterministic, no LLM; judge: named).
5. Statistical floor: k≥3; paired stats; pass^k; false-done; CI-aware phrasing.
6. Ablation ladder: per-task arm_config {name, config_digest, method_gates_mode, method_evidence_profile,
   env, expected_token_buckets} in every task record.
7. Fail-closed scoring + void protocol: any condition missing ⇒ benchmark-void, numbers not citable.
