# Historical pilot — economics of 100,000 tasks

> This file preserves the earlier one-response pilot. It is not the current
> tool-use result. The corrected tool pilot passed 90/90 workflows; GPT
> passed 18/18. See [the corrected tool report](toolloop/REPORT.md).
>
> The ten-repetition campaign is still running. The current task comparison
> is in [the interactive report](report.html). GitHub contains a dated
> snapshot, not a live connection to the local worker.

Catalog date: `2026-10-16`. Completed objective runs: **210**.

The main unit is one task. All costs below are scaled to 100,000 attempts or 100,000 successful tasks.

## Task economics

Each cell shows `passes/runs; cost per 100,000 successful tasks`. A zero-pass cell shows the cost per 100,000 attempts and states that the successful-task cost is undefined.

The three tool rows are one-shot tool-plan tasks. The harness did not execute tool calls or return tool results.

| Task | DS LunaRoute | GLM 5.3 LunaRoute | GLM 5.3 Flash LunaRoute | Muse LunaRoute | DS OR price-first | DS Pro OR price-first | GPT-6 Luna | DS OR default | DS Pro OR default | GPT-6.1 Sol | Claude Haiku | Claude Sonnet | Claude Opus | GPT-6 Astra | Claude Fable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| reasoning/r1_tiling | 0/2; no success ($1.741 / 100K attempts) | 1/2; $3.323 / 100K successes | 2/2; $0.405 / 100K successes | 2/2; $2.779 / 100K successes | 0/2; no success ($62.020 / 100K attempts) | 1/2; $2,466.59 / 100K successes | 2/2; $142.415 / 100K successes | 0/2; no success ($62.020 / 100K attempts) | 1/2; $3,325.07 / 100K successes | 2/2; $1,450.30 / 100K successes | 2/2; $157.886 / 100K successes | 2/2; $1,170.10 / 100K successes | 2/2; $2,826.56 / 100K successes | 2/2; $7,101.50 / 100K successes | 2/2; $7,021.55 / 100K successes |
| reasoning/r2_expectedflips | 2/2; $0.268 / 100K successes | 2/2; $0.211 / 100K successes | 2/2; $0.259 / 100K successes | 2/2; $0.602 / 100K successes | 2/2; $8.489 / 100K successes | 2/2; $103.570 / 100K successes | 2/2; $15.595 / 100K successes | 2/2; $47.522 / 100K successes | 2/2; $443.200 / 100K successes | 2/2; $315.400 / 100K successes | 2/2; $32.288 / 100K successes | 2/2; $479.076 / 100K successes | 2/2; $1,424.46 / 100K successes | 2/2; $1,639.50 / 100K successes | 2/2; $2,237.13 / 100K successes |
| reasoning/r3_die_expected | 2/2; $0.214 / 100K successes | 2/2; $0.286 / 100K successes | 2/2; $0.253 / 100K successes | 2/2; $0.530 / 100K successes | 2/2; $9.725 / 100K successes | 2/2; $183.149 / 100K successes | 2/2; $16.860 / 100K successes | 2/2; $9.966 / 100K successes | 2/2; $135.726 / 100K successes | 2/2; $448.700 / 100K successes | 2/2; $39.621 / 100K successes | 2/2; $446.898 / 100K successes | 2/2; $1,698.76 / 100K successes | 2/2; $2,436.00 / 100K successes | 2/2; $2,751.44 / 100K successes |
| reasoning/r4_catalan | 2/2; $0.772 / 100K successes | 2/2; $0.353 / 100K successes | 2/2; $0.235 / 100K successes | 2/2; $0.779 / 100K successes | 2/2; $44.492 / 100K successes | 1/2; $1,082.39 / 100K successes | 2/2; $24.445 / 100K successes | 2/2; $157.902 / 100K successes | 2/2; $4,266.74 / 100K successes | 2/2; $543.400 / 100K successes | 2/2; $51.489 / 100K successes | 2/2; $692.185 / 100K successes | 2/2; $1,843.30 / 100K successes | 2/2; $3,537.00 / 100K successes | 2/2; $2,928.15 / 100K successes |
| tool-use/t1_orchestrate | 2/2; $0.620 / 100K successes | 0/2; no success ($0.375 / 100K attempts) | 2/2; $0.398 / 100K successes | 1/2; $2.990 / 100K successes | 2/2; $10.778 / 100K successes | 2/2; $82.726 / 100K successes | 0/2; no success ($17.875 / 100K attempts) | 2/2; $48.741 / 100K successes | 2/2; $213.492 / 100K successes | 0/2; no success ($300.000 / 100K attempts) | 1/2; $117.116 / 100K successes | 2/2; $911.625 / 100K successes | 2/2; $1,827.47 / 100K successes | 0/2; no success ($1,852.50 / 100K attempts) | 2/2; $5,138.38 / 100K successes |
| tool-use/t2_toolselect | 0/2; no success ($0.492 / 100K attempts) | 0/2; no success ($0.406 / 100K attempts) | 0/2; no success ($0.425 / 100K attempts) | 0/2; no success ($0.728 / 100K attempts) | 0/2; no success ($15.498 / 100K attempts) | 0/2; no success ($44.891 / 100K attempts) | 0/2; no success ($6.730 / 100K attempts) | 0/2; no success ($24.213 / 100K attempts) | 0/2; no success ($249.053 / 100K attempts) | 0/2; no success ($118.600 / 100K attempts) | 0/2; no success ($30.542 / 100K attempts) | 0/2; no success ($454.705 / 100K attempts) | 0/2; no success ($1,019.13 / 100K attempts) | 0/2; no success ($593.000 / 100K attempts) | 0/2; no success ($2,452.88 / 100K attempts) |
| tool-use/t3_inventory | 2/2; $0.566 / 100K successes | 0/2; no success ($0.339 / 100K attempts) | 2/2; $0.348 / 100K successes | 1/2; $2.134 / 100K successes | 2/2; $11.438 / 100K successes | 1/2; $418.178 / 100K successes | 0/2; no success ($15.295 / 100K attempts) | 2/2; $107.800 / 100K successes | 1/2; $618.128 / 100K successes | 0/2; no success ($293.400 / 100K attempts) | 2/2; $72.494 / 100K successes | 2/2; $1,171.37 / 100K successes | 2/2; $2,593.82 / 100K successes | 0/2; no success ($1,434.50 / 100K attempts) | 2/2; $4,873.05 / 100K successes |

## Route aggregate

This table combines both effort levels and all seven tasks. The tool rows still use the one-shot tool-plan contract.

| Route | Passes | Pass rate | Cost / 100K attempts | Cost / 100K successes | Median seconds |
|---|---:|---:|---:|---:|---:|
| GLM 5.3 Flash — LunaRoute | 12/14 | 86% | $0.332 | $0.387 | 10.0 |
| DeepSeek V4.1 Flash — LunaRoute | 10/14 | 71% | $0.667 | $0.934 | 2.4 |
| GLM 5.3 — LunaRoute | 7/14 | 50% | $0.519 | $1.038 | 4.3 |
| Muse Spark Open — LunaRoute | 10/14 | 71% | $1.140 | $1.596 | 4.7 |
| DeepSeek V4.1 Flash — OpenRouter price-first | 10/14 | 71% | $23.206 | $32.488 | 3.8 |
| GPT-6 Luna — OpenAI API | 8/14 | 57% | $34.174 | $59.804 | 4.3 |
| Claude Haiku 5.5 — OpenRouter | 11/14 | 79% | $63.268 | $80.523 | 5.0 |
| DeepSeek V4.1 Flash — OpenRouter | 10/14 | 71% | $65.452 | $91.633 | 3.5 |
| DeepSeek V4 Pro 0813 — OpenRouter price-first | 9/14 | 64% | $342.559 | $532.870 | 23.2 |
| GPT-6.1 Sol — OpenAI API | 8/14 | 57% | $495.686 | $867.450 | 7.6 |
| Claude Sonnet 5.5 — OpenRouter | 12/14 | 86% | $760.851 | $887.659 | 3.7 |
| DeepSeek V4 Pro 0813 — OpenRouter | 10/14 | 71% | $1,039.97 | $1,455.96 | 15.3 |
| Claude Opus 5.5 — OpenRouter | 12/14 | 86% | $1,890.50 | $2,205.58 | 7.5 |
| Claude Fable 5.1 — OpenRouter | 12/14 | 86% | $3,914.65 | $4,567.09 | 8.0 |
| GPT-6 Astra — OpenAI API | 8/14 | 57% | $2,656.29 | $4,648.50 | 9.1 |

## Catalog price points

List prices are USD per one million tokens. OpenRouter cash purchases add the configured 5.5% credit fee.

| Model and route | Input | Output | Bench status |
|---|---:|---:|---|
| DeepSeek V4.1 Flash — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |
| GLM 5.3 — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |
| GLM 5.3 Flash — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |
| Muse Spark Open — LunaRoute | $0.004167 allocated per 1M total | $0.004167 allocated per 1M total | Tested |
| GPT-6 Luna — OpenAI API | $0.10 | $0.50 | Tested |
| Claude Haiku 5.5 — OpenRouter | $0.10 | $0.50 | Tested |
| DeepSeek V4.1 Flash — OpenRouter | $0.15 | $0.60 | Tested |
| DeepSeek V4 Pro 0813 — OpenRouter | $0.66 | $1.98 | Tested: default and price-first |
| GPT-6.1 Sol — OpenAI API | $2.00 | $10.00 | Tested |
| Claude Sonnet 5.5 — OpenRouter | $2.00 | $10.00 | Tested |
| Claude Opus 5.5 — OpenRouter | $4.00 | $20.00 | Tested |
| GPT-6 Astra — OpenAI API | $10.00 | $50.00 | Tested |
| Claude Fable 5.1 — OpenRouter | $10.00 | $50.00 | Tested |

DeepSeek and Claude runs use OpenRouter. GPT runs use the direct OpenAI Responses API.

## LunaRoute catalog review

The authenticated live main catalog has 13 entries. Background entries change scheduler priority; they are not separate quality models.

| Catalog entry | Type | Benchmark decision |
|---|---|---|
| `deepseek-4.1-flash` | Chat | Already tested |
| `glm-5.3` | Chat | Tested in main text benchmark |
| `glm-5.3-flash` | Chat speed variant | Tested in main text benchmark |
| `muse-spark-open` | Chat | Tested in main text benchmark |
| Four `-background` chat entries | Lower-priority scheduler variants | Test once under sustained load |
| `glm-5.3-vision` and `glm-5.3-vision-background` | Vision variants | Defer until image-input tasks exist |
| `clef-flash` and `djev` | System One decision models | Use a separate routing and triage benchmark |
| `whisper-large-v3` | Transcription | Exclude from this text benchmark |

The separate LunaRoute catalogs contain four image models, four embedding models, and one reranker. They need task-specific benchmarks and are outside the current text and coding scope.

## Findings

- Task type changes the economic result. Use task-level cost and success thresholds for route selection.
- GPT-6 Luna, GPT-6.1 Sol, and GPT-6 Astra passed all eight reasoning runs.
- GLM 5.3 Flash, Claude Sonnet 5.5, Claude Opus 5.5, and Claude Fable 5.1 each completed 12 of 14 one-shot runs. This is the highest aggregate result in the present data.
- GPT-6 Luna, GPT-6.1 Sol, and GPT-6 Astra failed all six one-shot tool-plan runs. The harness did not run a real tool loop, so this is not a general tool-use result.
- Across all 61 graded base failures, the enforced Aegis retry recovered 18 tasks. All 61 evidence journals verified.
- OpenRouter price-first routing cut observed DeepSeek cash cost by 65% and changed median latency by +11% against default routing.
- In the objective scale, OpenRouter default routing used six upstream providers. Price-first routing used two. These runs use provider-reported cost.
- DeepSeek Pro default completed 10 of 14 base runs. Price-first completed 9 of 14. Price-first reduced aggregate cash cost, but it also reduced the observed pass count.

## LunaRoute accounting note

The fixed plan is $500 per month. The supplied full-capacity assumption is 4 billion reported tokens per 24 hours for 30 days. This gives 120.0 billion monthly tokens and an allocated cost of $0.004167 per one million total tokens.

LunaRoute has zero marginal cash cost for an included request. The task tables use allocated plan cost so the route remains comparable with token-billed routes.

## Aegis Method Lite failure retries

A base failure triggers one paired retry with the exact Aegis Method Lite payload in the system prompt. Base and retry results remain separate.

| Route | Retries | Recovered | Recovery rate | Failed-base tokens | Aegis tokens | Incremental cost / 100K retries |
|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1 — OpenRouter | 2 | 0 | 0% | 3,322 | 5,479 | $4,213.14 |
| Claude Haiku 5.5 — OpenRouter | 3 | 1 | 33% | 5,339 | 8,950 | $59.523 |
| Claude Opus 5.5 — OpenRouter | 2 | 0 | 0% | 3,358 | 0 | $0.000000 |
| DeepSeek V4 Pro 0813 — OpenRouter | 4 | 1 | 25% | 27,051 | 28,520 | $847.816 |
| DeepSeek V4 Pro 0813 — OpenRouter price-first | 5 | 3 | 60% | 35,941 | 31,603 | $426.246 |
| GLM 5.3 Flash — LunaRoute | 2 | 0 | 0% | 2,042 | 3,250 | $0.677 |
| GLM 5.3 — LunaRoute | 7 | 3 | 43% | 6,426 | 12,683 | $0.755 |
| GPT-6 Astra — OpenAI API | 6 | 0 | 0% | 3,608 | 12,304 | $6,262.75 |
| GPT-6 Luna — OpenAI API | 6 | 0 | 0% | 3,652 | 8,352 | $29.694 |
| Muse Spark Open — LunaRoute | 4 | 1 | 25% | 11,852 | 11,641 | $1.213 |

The Aegis retry is an intervention result. It does not replace the base score. For one-shot tasks, the payload is prompt guidance without file or shell enforcement.

## Enforced Aegis Method failure retries

The provider-neutral benchmark adapter keeps each original provider route. It validates `.am` plan and child contracts before the request, runs the existing task checker as the falsifier, validates completion and closure with Aegis Method 0.3.0, and writes an isolated signed Aegis evidence journal.

This is a benchmark-native reimplementation. It does not claim native Codex-hook or Claude-hook transport equivalence.

Recovered **18 of 61** failed base tasks. **61 of 61** signed journals verified.

| Route | Retries | Recovered | Recovery rate | Failed-base tokens | Enforced tokens | Incremental cost / 100K retries |
|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1 — OpenRouter | 2 | 0 | 0% | 3,322 | 9,884 | $5,808.83 |
| Claude Haiku 5.5 — OpenRouter | 3 | 1 | 33% | 5,339 | 15,580 | $75.482 |
| Claude Opus 5.5 — OpenRouter | 2 | 0 | 0% | 3,358 | 9,906 | $2,346.74 |
| Claude Sonnet 5.5 — OpenRouter | 2 | 0 | 0% | 3,254 | 9,957 | $1,188.46 |
| DeepSeek V4.1 Flash — LunaRoute | 4 | 2 | 50% | 10,718 | 24,114 | $2.512 |
| DeepSeek V4.1 Flash — OpenRouter | 4 | 2 | 50% | 10,701 | 28,976 | $367.085 |
| DeepSeek V4.1 Flash — OpenRouter price-first | 4 | 2 | 50% | 11,070 | 26,452 | $268.182 |
| DeepSeek V4 Pro 0813 — OpenRouter | 4 | 2 | 50% | 27,051 | 22,821 | $419.507 |
| DeepSeek V4 Pro 0813 — OpenRouter price-first | 5 | 2 | 40% | 35,941 | 37,376 | $419.994 |
| GLM 5.3 Flash — LunaRoute | 2 | 0 | 0% | 2,042 | 6,405 | $1.334 |
| GLM 5.3 — LunaRoute | 7 | 5 | 71% | 6,426 | 23,285 | $1.386 |
| GPT-6 Astra — OpenAI API | 6 | 0 | 0% | 3,608 | 16,796 | $4,107.17 |
| GPT-6 Luna — OpenAI API | 6 | 0 | 0% | 3,652 | 16,683 | $40.130 |
| GPT-6.1 Sol — OpenAI API | 6 | 0 | 0% | 3,480 | 16,458 | $765.100 |
| Muse Spark Open — LunaRoute | 4 | 2 | 50% | 11,852 | 18,610 | $1.939 |

A failed falsifier leaves the child open. The completion and closure gates block the success claim. A passed retry closes only when the plan, completion, closure, and evidence-journal checks all pass.

## Sandboxed coding pilot

This pilot uses one coding task and one high-effort run per route. It is separate from the 210-run objective scale.

| Route | Status | Hidden tests | Calls | Reported tokens | Cost / 100K attempts | Cost source | Seconds |
|---|---|---:|---:|---:|---:|---|---:|
| Claude Sonnet 5.5 — OpenRouter | Fail | 3/4 passed | 7 | 100149 | $5,579.11 | catalog-estimate | 32.6 |
| DeepSeek V4.1 Flash — LunaRoute | Fail | 3/4 passed | 10 | 172658 | $71.941 | full-capacity allocation | 70.7 |
| DeepSeek V4.1 Flash — OpenRouter price-first | Fail | 3/4 passed | 15 | 431701 | $942.163 | advertised-floor-estimate | 402.4 |
| GPT-6.1 Sol — OpenAI API | Fail | 3/4 passed | 36 | 480293 | $11,603.96 | list-price | 178.2 |

The pilot uses an operating-system file sandbox. The sandbox blocks the source benchmark, hidden tests, and reference files during the model run.
Earlier pilot attempts exposed those files. They are marked invalid and excluded from this table.
All four routes failed the same concurrent audit consistency test. Each route passed the other three hidden tests.
Cost per 100,000 successful coding tasks is undefined because no route passed all four hidden tests.

## Bench expansion order

### Testable — repair the tool journey

- Promise: one real tool task runs end to end on each current route.
- Journey: prompt, tool call, deterministic tool result, model continuation, final answer, grade, and total cost.
- Threshold: 100% harness completion with no provider-format exception and a reconciled cost record.
- Falsifier: the providers need different task contracts that cannot be normalized.
- Rule: stop model expansion if this gate fails. Repair the harness first.

### Usable — add the price ladder

- Repeat all 15 active routes three times.
- Keep DeepSeek and Claude on OpenRouter. Keep GPT on the direct OpenAI Responses API.
- Run LunaRoute background variants in a separate sustained-load slice.
- Run three repetitions on representative reasoning, real tool-loop, and coding tasks.
- Report cost per 100,000 attempts, pass rate, cost per 100,000 successes, and latency.
- Reconcile OpenRouter provider receipts and refusals before using fine cost differences for a route decision.

### Lovable — select a route for a workload

- Let the user set a task mix, minimum success rate, and maximum latency.
- Return the lowest-cost route that meets the threshold.
- Continue only after users repeat this decision or prefer it to the current spreadsheet workflow.

## Interpretation limits

- LunaRoute allocation assumes sustained full use: 120 billion reported tokens per 30-day month.
- The LunaRoute token basis assumes reported input plus output tokens. Reconcile this with the plan ledger.
- OpenRouter cash cost applies the 5.5% Standard credit-purchase fee. The fee is not an inference-line item.
- The earlier Aegis Method Lite arm covered 41 failures and recovered nine. The enforced arm covered all 61 failures and recovered 18. These are single stochastic retries, not a causal estimate.
- The OpenRouter price-first coding cost is an advertised-floor estimate. The generation receipt endpoint did not return the per-call receipts.
- One uncapped OpenRouter price-first long-task request was stopped after more than three minutes. It has no usage receipt and is not in the totals.
- The objective set has one low-effort and one high-effort run per route and task. This is not enough for a stable quality or latency rank.
- The benchmark measures this task set and harness. It does not prove a general model rank.
