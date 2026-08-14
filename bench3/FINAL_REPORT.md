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


## Findings (draft — pilot in progress)

### Where the arms separate

Two of twelve tasks discriminate; the rest saturate (every arm solves
them, differing only in time and cost).

**r1_tiling** (3x30 domino tilings = 299,303,201): the reasoning ladder.
deepseek-v4-flash 0/3 — at `high` effort it burns its entire output
budget (20K tokens) on reasoning and never converges. deepseek-v4-pro
2/3 — converges in 137-216s. grok-4.6 3/3 (121-154s). gpt-5.6-sol 3/3 in
37-42s, the fastest and cheapest correct solver on this task.

**t1_orchestrate** (emit a full multi-call tool sequence in one shot):
deepseek-v4-pro 3/3, deepseek-v4-flash 2/3, gpt-5.6-sol 0/3, grok-4.6
0/3. The two failures are qualitatively different: gpt-5.6-sol emits the
first wave of calls and stops (expecting execution); grok-4.6 emits the
whole plan as JSON *prose* instead of function calls.

**t2_toolselect** (choose from 12 tools, avoid decoys, full sequence):
0/x on every arm — a universal ceiling for single-shot multi-call
planning in this format. Multi-turn tool use is tested properly by the
agentic tasks, which all arms solve.

### Agentic coding and workflows: saturated

c1_deadlock (3 planted concurrency bugs), c2_perf (O(n·w) to sub-
quadratic), a1_chained (4 masked defects incl. stale-schema migration),
a2_buildtestfix (fix + write your own tests): all arms pass everything
run so far. The differences are cost and time: deepseek-v4-flash is the
cheapest per run ($0.006-0.007 on c1/c2), gpt-sol the most expensive
($0.19 on a1) but its agent loop is heavily cached-input (169K cached vs
45 fresh tokens) so the marginal cost of long iterations is lower than
the sticker price suggests. grok was the fastest on a1_chained (43s).

### Cost per passing task

| arm | cost / passing task |
|---|---|
| deepseek-v4-flash | $0.003 |
| deepseek-v4-pro | $0.006 |
| grok-4.6 | $0.015 |
| gpt-5.6-sol | $0.049 |

gpt-5.6-sol is ~16x flash and ~3x grok per passing task at list prices.

### Subjective quality (creativity + writing) and judge bias

| arm | v4-pro judge | gpt-5.6-sol judge |
|---|---|---|
| deepseek-v4-flash | 4.36 | 3.65 |
| deepseek-v4-pro | 4.39 | 3.55 |
| gpt-5.6-sol | 4.37 | 4.23 |
| grok-4.6 | 3.93 | 3.39 |

The two judges disagree in level and rank: deepseek-v4-pro compresses all
arms to ~4.0-4.4, while gpt-5.6-sol spreads them 3.4-4.2 with gpt-sol
first. That pattern is consistent with each judge favouring its own
vendor's prose (blind judging removes the *label*, not the style
preference). The only arm both judges agree on is **grok: lowest on
subjective quality by both** (3.93 / 3.39) — a robust finding.

Per-criterion agreement between judges: 41% exact, 86% within 1 point.

## Full results

# DeepSeek / OpenAI / xAI — three-provider benchmark (bench3)

**Status:** 128 runs, $3.8305 total spend (list prices).

## Totals

| arm | runs | pass | pass % | wall s | cost $ | in tok | out tok | reas tok |
|---|---|---|---|---|---|---|---|---|
| DeepSeek V4 Flash | 32 | 25 | 78 | 1727 | 0.0739 | 133100 | 176517 | 140063 |
| DeepSeek V4 Pro | 32 | 28 | 88 | 2023 | 0.2157 | 115588 | 174249 | 136961 |
| GPT-5.6 Sol | 32 | 25 | 78 | 1439 | 2.8702 | 5292 | 66284 | 17877 |
| Grok 4.6 | 32 | 26 | 81 | 1993 | 0.6707 | 202623 | 21873 | 66794 |

## Pass rate by category

| category | DeepSeek V4 Flash | DeepSeek V4 Pro | GPT-5.6 Sol | Grok 4.6 |
|---|---|---|---|---|
| Coding | 4/4 | 4/4 | 4/4 | 4/4 |
| Agentic workflow | 4/4 | 4/4 | 3/4 | 4/4 |
| Tool use | 2/6 | 3/6 | 0/6 | 0/6 |
| Reasoning | 3/6 | 5/6 | 6/6 | 6/6 |
| Creativity | 6/6 | 6/6 | 6/6 | 6/6 |
| Writing quality | 6/6 | 6/6 | 6/6 | 6/6 |

## Difficulty ladder (hardest first)

| task | difficulty | discrim | DeepSeek V4 Flash | DeepSeek V4 Pro | GPT-5.6 Sol | Grok 4.6 |
|---|---|---|---|---|---|---|
| tool-use/t2_toolselect | 1.00 | 0.00 | 0% | 0% | 0% | 0% |
| tool-use/t1_orchestrate | 0.58 | 1.00 | 67% | 100% | 0% | 0% |
| reasoning/r1_tiling | 0.33 | 1.00 | 0% | 67% | 100% | 100% |
| a2_buildtestfix | 0.12 | 0.50 | 100% | 100% | 50% | 100% |
| writing/w2_rewrite | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| writing/w1_explain | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| reasoning/r2_expectedflips | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| creativity/k2_story | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
| creativity/k1_product | 0.00 | 0.00 | 100% | 100% | 100% | 100% |
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
| DeepSeek V4 Flash | 0.0030 |
| DeepSeek V4 Pro | 0.0077 |
| GPT-5.6 Sol | 0.1148 |
| Grok 4.6 | 0.0258 |

_Generated by bin/report.py — raw data in results/, judged.csv, runs/._
