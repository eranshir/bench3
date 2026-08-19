# Plan: Aegis guided-vs-enforced run in bench3

**Status:** IMPLEMENTATION IN PROGRESS · **Date:** 2026-08-19
**Progress:** P0 ✅ · P1 ✅ · P2 ✅ · P3 ✅ (contamination.py, cohort manifest, parity/tokens/
isolation in every record; runner fixed: DSH_HOME isolation, credential export, pre-run clean-before) ·
P4 ✅ (aegis_metrics.py — pass@1/pass^k/compliance/enforcement-lift with McNemar + bootstrap) ·
**P5 RUNNING:** full matrix (6 models × 5 agentic × guided+enforced × k=3) executing in background
(staged cloud-first, resumable). Report pending matrix completion.
**Goal:** Run the complete bench3 matrix twice — once **guided** by the Aegis method (method prose in the
agent's context, no enforcement) and once **enforced** by the Aegis method (same instructions + a live gate
that blocks non-method-compliant mutations) — across all bench3 problems and models, under ADR 0043 validity.

---

## 1. Research summary — what the Aegis method is

Sources: mithran-hq/aegis (engine repo; mithran-business only points at it — D194), mithran-hq/aegis-method
(SPEC), ADR 0043, BENCHMARK_VALIDITY_STANDARD.md, smoke5 worked run, K10 preregistration, issue #1623.

**The method** (SPEC §5): five mandatory compiler passes, each with a **refusal mode** the harness enforces:

| Move | Requirement | Refusal |
|---|---|---|
| 1 · Evidence Before Architecture | snapshot current behavior/evidence into IR | architecture before evidence → rolled back |
| 2 · Strategy Before Plan | decisions + **assumption ledger** in IR | plans before strategy = "precise nonsense" |
| 3 · Issues As Memory | parent + children with scope/acceptance/owner | chat-only work "does not exist" |
| 4 · Falsification Before Confidence | each child has ≥1 **falsifier** (check + expected outcome) | child without falsifier is "not buildable" |
| 5 · Closure Against Reality | acceptance reconciled vs landed state | "done" without reconciliation is a lie |

**The arms** (ADR 0043 Rule 6 ladder): vanilla / aegis-contain / aegis-prose (guided) /
aegis-gates (enforced) / aegis-judge (+escalation). The K10 prereg states the design crisply:
**guidance vs enforced — identical instructions, the only difference is whether the enforcement gate is live.**

**The gate** (precedent: codex_swebench_pro_lima_gate_hook.py, a Codex PreToolUse hook): denies
write/edit/apply_patch until the workspace-local Aegis IR passes aegis-method validate plan --ir <ws>
— a schema-valid plan.json (with assumption ledger) + children/*.json each with
id/scope/acceptance/falsifiers[id, description, check{command, expected_outcome}]/status. Every decision is
appended to a **gate transcript** (gate-events.jsonl). Modes: strict (block) / soft (degrade) / hardened /
spine (host-backed session state + drift tripwire). "Marker counts are not evidence" — it validates against
the real artifact contract, not a presence check.

**The honest baseline (#1623):** the original campaign overclaimed; the corrected record says the supported
conclusion is *procedural* — "Aegis can require and record plans, frozen commitments, evidence, and closure
attempts. This campaign does not establish that Aegis makes an agent reliable, correct, or complete."
The smoke5 run showed **prose alone moved nothing** (identical resolve vectors, +43% tokens); the
**enforcement rungs never ran** (blocked on #1285 in the codex-native path). Our bench3 run is exactly that
missing measurement — and bench3 CAN run it because DSH's permission/sandbox layer is interceptable.

---

## 2. The comparison we will run

Two new arms in bench3, on every model and every task:

- **aegis-guided** (aegis-prose equivalent): the agent receives the method instructions as prose
  (the delivery contract: "author a .bruno/ train — plan with assumption ledger, child slices each with a
  falsifier, one commit per child, closure records"). No gate. The harness *records* compliance artifacts
  but does not block.
- **aegis-enforced** (aegis-gates equivalent): the **identical** instructions, plus a live gate that
  denies mutating tool calls until the workspace's method IR validates (same contract as the codex gate),
  with a per-run gate transcript.

Optional third arm (control): **vanilla** (no method text) so the guided-vs-enforced contrast can be read
against the no-method baseline — matches the ladder's Rule 6. (Decide at pre-registration; the core claim
is guided-vs-enforced.)

**Task scope.** True enforcement (deny mutations until plan/falsifiers exist) applies to **agentic tasks**
— coding (c1_deadlock, c2_perf, c3_adversarial) and agentic-workflow (a1_chained, a2_buildtestfix) = 5 tasks,
the only surface with a tool loop. For the 11 singleshot tasks (single-prompt API calls, no mutations), the
plan: run **guided** on all of them (method instructions injected into the prompt) and **enforced** as a
harness-side compliance gate on the response (the run FAILS if the response does not carry the method
artifacts: plan, falsifiers, closure). This keeps the "entire set of problems" promise while being explicit
that the mutation-gate only has meaning in agentic tasks. (Alternative — agentic-only enforcement — is the
fallback if the response-gate proves too brittle; decided at pre-registration.)

---

## 3. ADR 0043 validity → bench3 enforcement

Every condition must be enforced by the harness, not by report-time judgment:

| Rule | bench3 mechanism |
|---|---|
| 1 · Arm isolation | New workdir per (arm × repetition); fail-closed git status --porcelain empty + HEAD==base before agent starts; cross-arm added-line containment detector on output patches (calibrated threshold, default 0.20); cohort manifest (task ids, prompt SHA) committed to bench3/cohorts/. |
| 2 · Materialization proof | Per-task record stores: guided → the **payload digest** of the injected instructions read back from the session (release_id != unconfigured); enforced → the **gate transcript** with expected phase verdicts; control → proven absence via explicit config (AEGIS_BENCH_CONTROL_ARM-style env). Marker counts are not evidence. |
| 3 · Parity manifest | One pinned agent harness + one model per arm, real versions recorded per task (never placeholders). The gate validator is a bench3-pinned binary/package with its own recorded digest — it will NOT match the aegis product release digest; that divergence is recorded (Rule 3 allows inherent differences, isolated and reported). |
| 4 · Unified token rule | Existing bench3 accounting (input/cached/output/reasoning per run) applied identically to both arms; any auxiliary LLM calls (judge, compliance scorer) in named buckets; an expected bucket reporting unavailable invalidates the run. |
| 5 · Statistical floor | k ≥ 3 reps per (task × arm); paired per-task stats — McNemar on resolution, bootstrap CIs on tokens/time; report pass@1, pass^k (all k), false-done calibration, tokens/resolved, wasted-token fraction; no causal phrasing where CI includes 0. |
| 6 · Ablation ladder | Per-task arm_config block: name, config_digest, method_gates_mode, method_evidence_profile, env, expected_token_buckets — matching the smoke5 record shape; registry digests in the validity block. |
| 7 · Fail-closed scoring + void | Reuse bench3 hidden-test scoring; timeouts = unresolved; any validity failure marks the run benchmark-void with a VOID marker and no citable numbers. |

---

## 4. Implementation phases

**P0 · Pre-registration (before any data).** Freeze: arms, task list, model list, k, gate contract, metric
set, decision rule (e.g., "enforcement lift = enforced fully_compliant − guided fully_compliant; TRUE iff
bootstrap CI excludes 0"), and the honesty boundary ("we measure whether live enforcement changes measured
adherence/outcomes on bench3; we do not claim it makes models reliable"). Save as
bench3/aegis/PREREGISTRATION.md with a commit hash, mirroring AEGIS_CLAUDE_K10_PREREGISTRATION.md.

**P1 · Method payload (guided arm).** Distill the Five Moves + delivery contract into a fixed instruction
block (the DELIVERY_INSTRUCTION precedent): plan with assumption ledger; children with
id/scope/acceptance/falsifiers[check{command,expected_outcome}]; one commit per child; closure records;
"done requires reconciliation". Wire into the DSH headless prompt (system layer) for agentic runs and into
the singleshot request system prompt. Hash the exact text → the materialization digest.

**P2 · Gate (enforced arm) — the core build.** Implement the PreToolUse equivalent in DSH:
- A bench3 **gate validator** implementing the bruno.local_ir.plan.v1 contract (plan + children +
  falsifiers; JSON-schema validated; same shape as the codex gate's aegis-method validate). Pin and
  record its digest (Rule 3 divergence note).
- A **DSH permission-layer gate**: add an aegis-gate preset (or approval-policy wrapper) to the bench3
  isolated home (bench3/.dsh-home/settings.yaml) so that mutating tools (bash with write commands,
  write tool) are denied with a method-conformant reason until the validator passes; every decision
  appended to <workspace>/.bruno/gate-events.jsonl (the transcript). Modes: strict (default; soft as a
  pilot calibration). DSH's dsh-permission-presets service is the interception point (the bench3 home
  already pins permission presets).
- A **gate canary** (the codex gate ships one): a first-action Write attempt must be denied pre-plan —
  proves the gate is live, not decorative.

**P3 · Validity plumbing (bench3/bin + runner changes).** New aegis_run.py (orchestrates guided/
enforced arms over the existing agentic/singleshot runners), workspace derivation + isolation proof,
contamination detector, arm_config + materialization proof writers, parity manifest, token buckets,
k-repetition orchestration, paired stats (McNemar + bootstrap), VOID protocol. Reuse the existing
results.csv schema extended with per-task arm_config + validity blocks (a companion JSONL per run,
not CSV columns).

**P4 · Scoring & compliance metrics.** Beyond pass/fail, compute the compliance vector (per #1629/#1630
scoped): plan present before first mutation; per-child falsifiers (count + validity); closure attempted/
reconciled; trail validity; false-done (final claim vs hidden-test verdict). Metrics engine mirrors the K10
list. Enforced-arm runs are scored on the same hidden tests as guided — the gate changes trajectory, not
the rubric.

**P5 · Run + report.** Cohort: all 6 models × 5 agentic tasks (guided+enforced) × k=3; singleshot: 11 tasks
× all models (guided + response-gate enforced) × k=3. Cost note: MTPLX agentic is ~20 min/run → the long
pole; proposal is full k=3 for cloud arms and MTPLX (flag if budget-constrained → k=3 but only the 5
agentic tasks, or accept a longer wall). Report mirrors the smoke5 format with the honesty framing.

---

## 5. Risks, inherited defects, and open questions

1. **Honesty boundary (#1623):** the deliverable claim is the enforcement-lift measurement on bench3,
   never "Aegis makes agents better". The corrected record's non-claims are adopted verbatim.
2. **Inherited instrument defects (children of #1623):** #1629 (score trail_valid on ONE rubric across
   arms — we implement one rubric from the start), #1630 (adherence per unit of work, not per turn — our
   compliance vector is per-task/artifact, not per-turn), #1636 (closure contract — we adopt the ADR 0059
   closure semantics). All three are in the metric spec, not post-hoc.
3. **Parity manifest vs am:** our gate validator is bench3-pinned, not the aegis release binary — Rule 3
   divergence recorded per task; the materialization proof names the pinned digest.
4. **Gate effectiveness on DSH:** the permission-layer interception must be verified with the canary
   before data collection; a fallback is a between-turn gate (validator runs after each tool turn; mutation
   results are rolled back/denied in the next turn) if hard pre-tool denial is not reachable in the DSH
   plugin surface.
5. **Singleshot "enforced":** the response-gate interpretation is the weakest rung; if it proves brittle,
   restrict enforcement claims to the agentic tasks and report singleshot as guided-only (documented at
   pre-registration).
6. **Cost/time:** k=3 × 2 arms × 5 agentic tasks × 6 models is the long pole (MTPLX especially); a
   staged run (cloud arms first, MTPLX last) keeps the measurement resumable.
7. **Open decisions for pre-registration:** include the vanilla control arm? singleshot enforced
   interpretation (response-gate vs guided-only)? k=3 vs k=5 on the discriminating tasks? MTPLX k=3?


---

## 6. Live status (checkpoint 2026-08-19)

- [x] **P0 Pre-registration** - PREREGISTRATION.md frozen (arms, k=3, gate contract, D1-D3, ADR checklist). Singleshot scope ratified: guided-only (response-gate proven brittle; models answer without .bruno artifacts).
- [x] **P1 Method payload** - method_payload.md (Five Moves + .bruno IR contract), digest pinned.
- [x] **P2 Gate** - gate_validator.py (exit 0 valid), gate_daemon.py (baseline commit, pre-commit hook, revert non-.bruno mutations, gate-events.jsonl), modes strict/soft.
- [x] **P3/P4 Plumbing & metrics** - aegis_run.py, aegis_singleshot.py, contamination.py, aegis_metrics.py (agentic-scoped), aegis_report.py; ADR field audit on 20 agentic records: payload digest 20/20, gate transcript 8/8 enforced (1 revert captured), isolation pre-clean 20/20, plan_valid 20/20, parity pinned (dsh 0.1.0-rc.6, single validator digest).
- [ ] **P5 Matrix run - IN PROGRESS** - 246 records (180 agentic + 66 singleshot) across 6 models / 5 agentic tasks / 11 singleshot; 67/246 at checkpoint; 4 parallel workers + singleshot worker; est. ~4h remaining.
- [ ] **Final report** - regenerate REPORT.md + FINAL_REPORT_DRAFT.md on full records; ADR 0043 7-rule checklist; honesty-framed verdict.
