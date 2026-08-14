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
