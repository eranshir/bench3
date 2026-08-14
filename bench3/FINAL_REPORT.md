# Three-provider coding-agent benchmark — final report

# Three-provider coding-agent benchmark — DeepSeek · OpenAI · xAI

## 1. Question and scope

Continuation of the repo's first benchmark (bench/), which compared
deepseek-v4-flash against gpt-5.6-sol through the Codex CLI. bench3 extends
the comparison to **four arms across three providers** — deepseek-v4-flash,
deepseek-v4-pro, gpt-5.6-sol, grok-4.6 — over **six task categories** (coding,
multi-step agentic workflow, multi-step reasoning, creativity, writing
quality, tool use), measuring ability to solve, solution quality, wall-clock
time, tokens, and cost, with tasks designed *hardest-but-smallest* and
laddered from hardest down.

## 2. Systems under test

| | deepseek-flash | deepseek-pro | gpt-sol | grok |
|---|---|---|---|---|
| Model | deepseek-v4-flash | deepseek-v4-pro | gpt-5.6-sol | grok-4.6 |
| Vendor | DeepSeek | DeepSeek | OpenAI | xAI |
| In $/M | 0.14 | 0.42 | 5.00 | 2.00 |
| Cached in $/M | 0.0028 | 0.0084 | 0.50 | 0.20 |
| Out $/M | 0.28 | 0.87 | 30.00 | 6.00 |

Both modes run identical prompts and tool surfaces for every arm; the only
per-arm differences are the model id and the wire spelling of the pinned
reasoning effort.

## 3. Harness

- **Agentic mode** (coding, agentic-workflow): DSH `headless` profile in an
  isolated `DSH_HOME` (`.dsh-home/`, gitignored). Same tool surface,
  sandbox, and system prompt for all four arms; effort pinned via
  `agent-default-model` settings; exact per-call usage parsed from the
  session transcript; full trajectories retained.
- **Single-shot mode** (reasoning, creativity, writing, tool use): one
  direct API client for all four arms; exact usage from each response;
  function calling via `tools.json` (gpt-5.6-sol tool tasks route through
  the Responses API — chat/completions rejects function tools with
  reasoning_effort).

## 4. Reasoning-effort policy

Pinned per task *type*, applied identically to all arms:

- **high** for objective reasoning, tool-use, coding, and agentic tasks.
- **off** (generation mode) for creativity and writing tasks, because
  deepseek-v4-flash at any enabled thinking effort burns its entire output
  budget on reasoning (measured: 16K reasoning tokens with zero content at
  high; 68K reasoning chars at low). Wire mapping: deepseek sends
  `thinking: disabled`; gpt/grok send `reasoning_effort: low`.

## 5. Grading

- Coding / agentic: blind hidden tests (fail-on-fixture and pass-on-
  reference validated for every task) plus diff review.
- Tool use / reasoning: deterministic checkers on the emitted call
  sequence / final answer.
- Creativity / writing: blind, shuffled rubric judging by deepseek-v4-pro
  (thinking disabled), with a gpt-5.6-sol cross-check on a sample.

## 6. Threats to validity

- n=3 per cell for single-shot tasks, n=2 for agentic: adequate for
  saturated comparisons, thin for one-run gaps.
- The judge is one model (deepseek-v4-pro); blind/shuffled judging removes
  self-preference but not judge taste. The gpt cross-check quantifies
  agreement on a sample.
- Task authorship bias: the suites were written by the same agent that
  analyses the results.
- Machine-relative timing (h1-style perf budgets absent here, but wall-clock
  is machine-relative by nature).
- DeepSeek pricing: a list-price increase was announced during the pilot
  (effective date pending); all DeepSeek costs use current list prices.
- gpt-sol runs bill against an API key here (real money), unlike the first
  benchmark where GPT ran on subscription quota.

_Narrative sections completed by bin/report.py from results/, judged.csv,_
_and runs/._

## Findings (expanded — 200 runs, 16 tasks)

### Where the arms separate

Five of sixteen tasks discriminate; the rest saturate (every arm solves
them, differing only in time and cost). The discriminating tasks cluster
in two domains: hard counting-reasoning, and single-shot multi-call tool
planning.

**Reasoning (n=5 on the hard ones):**

| task | flash | pro | grok | gpt-sol |
|---|---|---|---|---|
| r1_tiling (3x30 domino count) | 0/5 | 2/5 | 5/5 | 5/5 |
| r4_catalan (Dyck paths to (10,10)) | 2/3 | 1/3 | 3/3 | 3/3 |
| r3_die_expected (coupon collector) | 3/3 | 3/3 | 3/3 | 3/3 |

deepseek-v4-flash at high effort burns its whole output budget on
reasoning without converging (5/5 failures on r1, ~200s each, 20K
reasoning tokens). deepseek-v4-pro fails the same way 60% of the time on
r1 and 2/3 on r4 — the mechanism is reproducible on both DeepSeek arms.
grok and gpt-5.6-sol solve every reasoning task; gpt is 3-5x faster.

**Tool planning (single-shot, no execution):**

| task | flash | pro | grok | gpt-sol |
|---|---|---|---|---|
| t1_orchestrate (finance chain, n=5) | 4/5 | 5/5 | 0/5 | 0/5 |
| t3_inventory (order chain, n=3) | 3/3 | 3/3 | 2/3 | 0/3 |
| t2_toolselect (12 tools + decoys, n=5) | 0/5 | 0/5 | 0/5 | 0/5 |

The headline surprise, now measured across three task domains and ~13
attempts per arm: **DeepSeek models emit complete multi-call tool
sequences in one shot nearly every time (pro 13/13, flash 10/11), while
gpt-5.6-sol fails every attempt** — it stops after the first tool wave,
expecting results that never come. grok is inconsistent (2/13), sometimes
writing the plan as JSON prose instead of calling the tools. t2, which
adds decoys and a stricter sequence, is a universal ceiling (0/5 on every
arm).

**Agentic coding (n=2-3):** c1 (concurrency), c2 (perf rewrite), c3
(wrong-greedy fix), a1 (chained bugs) — all arms pass everything. The one
agentic discriminator is **a2_buildtestfix (fix a CSV parser + write your
own tests): gpt-5.6-sol 1/3** (reproducibly misses the trailing-blank-line
edge case), DeepSeek arms and grok 3/3.

### Overall (200 runs)

| arm | pass | pass % | cost | cost/pass |
|---|---|---|---|---|
| deepseek-v4-flash | 38/50 | 76% | $0.10 | $0.003 |
| deepseek-v4-pro | 40/50 | 80% | $0.33 | $0.008 |
| grok-4.6 | 39/50 | 78% | $0.86 | $0.022 |
| gpt-5.6-sol | 35/50 | 70% | $3.60 | $0.103 |

gpt-5.6-sol has the lowest pass rate on this benchmark's mix — its
single-shot tool-planning failures (0/13) and a2 weakness outweigh its
reasoning strength — and is ~38x flash per passing task. Total spend
~$5 for 200 runs.

### Subjective quality and judge bias

| arm | v4-pro judge | gpt-5.6-sol judge |
|---|---|---|
| deepseek-v4-flash | 4.36 | 3.65 |
| deepseek-v4-pro | 4.39 | 3.55 |
| gpt-5.6-sol | 4.37 | 4.23 |
| grok-4.6 | 3.93 | 3.39 |

The two judges disagree in level and rank: deepseek-v4-pro compresses all
arms to ~4.0-4.4, while gpt-5.6-sol spreads them 3.4-4.2 with gpt-sol
first — consistent with each judge favouring its own vendor's prose.
The only arm both judges agree on: **grok lowest on subjective quality**
(3.93 / 3.39). Per-criterion agreement: 41% exact, 86% within 1 point.

## Full results

# DeepSeek / OpenAI / xAI — three-provider benchmark (bench3)

**Status:** 200 runs, $4.8983 total spend (list prices).

## Totals

| arm | runs | pass | pass % | wall s | cost $ | in tok | out tok | reas tok |
|---|---|---|---|---|---|---|---|---|
| DeepSeek V4 Flash | 50 | 38 | 76 | 2491 | 0.1034 | 174620 | 258646 | 213192 |
| DeepSeek V4 Pro | 50 | 40 | 80 | 3326 | 0.3319 | 158415 | 281673 | 229981 |
| GPT-5.6 Sol | 50 | 35 | 70 | 1827 | 3.6035 | 8942 | 85586 | 25327 |
| Grok 4.6 | 50 | 39 | 78 | 2633 | 0.8595 | 261094 | 28737 | 98327 |

## Pass rate by category

| category | DeepSeek V4 Flash | DeepSeek V4 Pro | GPT-5.6 Sol | Grok 4.6 |
|---|---|---|---|---|
| Coding | 6/6 | 6/6 | 6/6 | 6/6 |
| Agentic workflow | 5/5 | 5/5 | 3/5 | 5/5 |
| Tool use | 7/13 | 8/13 | 0/13 | 2/13 |
| Reasoning | 8/14 | 9/14 | 14/14 | 14/14 |
| Creativity | 6/6 | 6/6 | 6/6 | 6/6 |
| Writing quality | 6/6 | 6/6 | 6/6 | 6/6 |

## Difficulty ladder (hardest first)

| task | difficulty | discrim | DeepSeek V4 Flash | DeepSeek V4 Pro | GPT-5.6 Sol | Grok 4.6 |
|---|---|---|---|---|---|---|
| tool-use/t2_toolselect | 1.00 | 0.00 | 0% | 0% | 0% | 0% |
| tool-use/t1_orchestrate | 0.55 | 1.00 | 80% | 100% | 0% | 0% |
| reasoning/r1_tiling | 0.40 | 1.00 | 0% | 40% | 100% | 100% |
| tool-use/t3_inventory | 0.33 | 1.00 | 100% | 100% | 0% | 67% |
| reasoning/r4_catalan | 0.25 | 0.67 | 67% | 33% | 100% | 100% |
| a2_buildtestfix | 0.17 | 0.67 | 100% | 100% | 33% | 100% |
| writing/w2_rewrite | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| writing/w1_explain | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| reasoning/r3_die_expected | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| reasoning/r2_expectedflips | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| creativity/k2_story | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| creativity/k1_product | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| c3_adversarial | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| c2_perf | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| c1_deadlock | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| a1_chained | 0.00 | 0.00 | 100% | 100% | 100% | 100% |

## Rubric-judged quality (creativity, writing)

| task | DeepSeek V4 Flash | DeepSeek V4 Pro | GPT-5.6 Sol | Grok 4.6 |
|---|---|---|---|---|
| creativity/k1_product | 3.87 | 4.00 | 4.27 | 3.73 |
| creativity/k2_story | 3.58 | 3.58 | 4.25 | 2.50 |
| writing/w1_explain | 4.50 | 4.33 | 5.00 | 4.58 |
| writing/w2_rewrite | 4.42 | 4.00 | 3.42 | 2.75 |

## Cost per passing task

| arm | cost/pass $ |
|---|---|
| DeepSeek V4 Flash | 0.0027 |
| DeepSeek V4 Pro | 0.0083 |
| GPT-5.6 Sol | 0.1030 |
| Grok 4.6 | 0.0220 |

_Generated by bin/report.py — raw data in results/, judged.csv, runs/._
