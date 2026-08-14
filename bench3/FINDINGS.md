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
