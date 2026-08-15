# MTPLX (Qwen 3.8 27B Optimized Speed, local) — bench3 results

**Date:** 2026-08-15 · **Harness:** bench3 (same tasks/checkers as the four cloud arms) · **Trial:** 1
**Hardware:** MacBook Pro M5 Max, 64 GB unified · **Runtime:** MTPLX 2.7.1, turbo MTP profile, depth 3
**Model:** Youssofal/Qwen3.8-27B-MTPLX-Optimized-Speed (20.4 GB, MLX, 4-bit dynamic quant)

## Overall

| Arm | Pass | Cost | Wall | Med/task |
|---|---|---|---|---|
| DeepSeek V4 Flash | 38/50 (76%) | $0.103 | 2491s | 7s |
| DeepSeek V4 Pro | 40/50 (80%) | $0.332 | 3326s | 17s |
| GPT-5.6 Sol | 35/50 (70%) | $3.60 | 1827s | 11s |
| Grok 4.6 | 39/50 (78%) | $0.86 | 2633s | 24s |
| **MTPLX (local)** | **12/16 (75%)** | **$0.00** | 6350s | 116s |

MTPLX pass rate (75% on trial 1) lands mid-pack — statistically comparable to the cloud
arms on capability, at zero marginal cost. Caveat: n=16 (one trial) vs n=50 (three trials);
c2_perf's only failure is a watchdog timeout, not a proven capability miss.

## Per-task (trial 1)

| Task | Type | Result | Time | Notes |
|---|---|---|---|---|
| c1_deadlock | coding/agentic | ✅ | 1391s | passed hidden tests; 24.6k out tokens |
| c2_perf | coding/agentic | ❌ | 1800s | watchdog timeout (30 min), 29k out tokens, 1 test failing at kill |
| c3_adversarial | coding/agentic | ✅ | 120s | |
| a1_chained | workflow/agentic | ✅ | 1283s | |
| a2_buildtestfix | workflow/agentic | ✅ | 278s | |
| r1_tiling | reasoning | ✅ | 546s | **flash 0%, pro 40%, gpt/grok 100%** |
| r2_expectedflips | reasoning | ✅ | 39s | |
| r3_die_expected | reasoning | ✅ | 26s | |
| r4_catalan | reasoning | ✅ | 96s | **flash 66%, pro 33%** |
| t1_orchestrate | tool-use | ❌ | 38s | gpt/grok also fail; flash 80%, pro 100% |
| t2_toolselect | tool-use | ❌ | 18s | universal failure (all arms 0%) |
| t3_inventory | tool-use | ❌ | 24s | model: "I can't make tool calls in this turn" |
| k1_product | creativity | ✅ | 113s | judged 4.2/5 |
| k2_story | creativity | ✅ | 295s | judged 3.5/5 |
| w1_explain | writing | ✅ | 28s | judged 4.75/5 |
| w2_rewrite | writing | ✅ | 257s | judged 4.5/5 |

**Judged quality (blind rubric, deepseek-v4-pro judge): MTPLX 4.24/5 (n=4)** vs
flash 4.36, pro 4.39, gpt 4.37, grok 3.93.

## Where it lands

- **Reasoning is the strength.** Passed the two hardest discriminators (r1_tiling,
  r4_catalan) that both DeepSeek arms fail — GPT/Grok territory. All 4 reasoning tasks passed.
- **Coding/agentic is capable but slow.** 4/5 passed, but agent loops take 10-23x the wall
  time of cloud arms (120-1391s vs 20-240s) because the model is extremely verbose
  (5-15k reasoning tokens per turn; 24-29k output tokens per task) and decodes at
  ~16-30 tok/s.
- **Tool use is the weakness.** 0/3. On t3 the model literally refused ("I can't make tool
  calls in this turn") when the prompt warned no tool results would be returned — a
  Qwen 3.8 interaction difference vs DeepSeek/Grok, which still emitted the call sequence.
  t1 multi-call orchestration also failed (shared with gpt/grok; DeepSeek passes).
- **Cost & privacy:** $0 marginal; fully local/offline. Every cloud arm costs
  $0.003-$0.10 per passing task.

## Tokens/sec reconciliation (vs the app dashboard's 46.4 tok/s)

The app dashboard measures **pure decode** on a cool machine. Measured on this M5 Max,
9000-token generations of the same HTML5-Canvas-Flappy-Bird prompt:

| Sampler | Decode tok/s | Notes |
|---|---|---|
| default (1.0/0.95/20), cool state | 36.2 | early run, machine still cool |
| greedy (temp 0), cool state | 41.2 | |
| default, hot (after ~2h load) | 25.7 / 25.9 | consistent, throttled |
| greedy, hot | 28.5 / 34.0 | |

Factors explaining the app's higher number:
1. **Thermal state (dominant):** the same request varies 24 → 41 → 46 tok/s purely with
   machine temperature; 2h of matrix load throttled the M5 Max. The app's 46.4 was a
   fresh/cool (possibly fan-boosted) run.
2. **Decode-only vs end-to-end:** the app reports decode; the harness numbers include
   prefill, queue, and agent-loop overhead.
3. **Sampler:** greedy was *faster* here (fewer verify cycles, 2411 vs 3104-3242) —
   the draft head's argmax matches the target's argmax at high rate; default-sampler runs
   do more rejection repair (1681-1915 corrections).

Direct MTP-vs-AR decode benchmark (temp 0, 1000 tokens): **MTP 22-30 tok/s vs AR 13-18
tok/s → 1.6-1.7x** (up to 2.6x in a cool burst).

## Harness notes

- MTPLX added as a 5th arm (provider `mtplx`, localhost:8000, prices 0) — see arms.yaml,
  run_singleshot.py, run_agentic.sh, .dsh-home/settings.yaml.
- Effort wiring: harness `high` → Qwen `xhigh`; harness `off` → Qwen `low`.
- Watchdog: cloud arms fit 900s; MTPLX needed LIMIT=1800 (c1 took 1391s). Fixed a
  harness bug (`timeout_${LIMIT}s` unbound variable under `set -u`).
- One transient server stall observed after a long turn (recovered on restart); a
  supervisor loop restarts the local server if it becomes unresponsive.
