
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

### Judge disagreement

deepseek-v4-pro rubric scores average 0.8 points higher than gpt-5.6-sol
on the same outputs (47% exact per-criterion agreement). Both judges are
reported everywhere; the webapp shows the spread per criterion. Treat
single-judge scores as having +/- 1 point of judge noise.
