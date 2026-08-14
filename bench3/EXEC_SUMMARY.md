## Executive summary (draft — data as of 2026-08-14)

Four arms — deepseek-v4-flash, deepseek-v4-pro, gpt-5.6-sol, grok-4.6 —
were run over twelve tasks in six categories through one harness (DSH
headless for agentic work, one direct API client for single-shot work),
with reasoning effort pinned per task type. 114 runs so far at a total
spend under $2.

1. **On accuracy, the models separate on exactly two tasks.** Everything
   hard-but-specified — concurrency, perf rewrites, chained bugs,
   test-driven implementation, writing, creativity — was solved by all
   arms. The only discrimination: r1_tiling (a 3x30 domino-tiling count)
   and the single-shot multi-call tool tasks.
2. **r1_tiling ranks the reasoning stacks.** deepseek-flash 0/3 (burns its
   whole output budget on reasoning without converging), deepseek-pro 2/3
   (slow, 137-216s), grok 3/3 (121-154s), gpt-5.6-sol 3/3 (fastest,
   37-42s).
3. **Single-shot multi-call planning fails on every arm** (t2_toolselect
   0/x everywhere; t1 only DeepSeek arms pass, and differently: pro emits
   the full chain, flash sometimes, gpt stops after one wave, grok emits
   the plan as prose instead of function calls). This is a format/ceiling
   finding, not a per-model quality ranking.
4. **Agentic coding/workflow tasks saturate — every arm solves all of
   them** (c1 concurrency, c2 perf rewrite, a1 chained bugs, a2 TDD),
   with gpt-sol the most token-efficient on the agent loop (mostly cached
   input) and deepseek the cheapest overall.
5. **Cost per passing task: flash $0.003, pro $0.006, grok $0.015,
   gpt-sol $0.049 (16x flash).** Total spend ~$1.5 for 115+ runs.
6. **Judge disagreement is real.** deepseek-v4-pro rubric scores run ~0.8
   points higher than gpt-5.6-sol on the same outputs (47% exact
   agreement); both are reported and the spread is shown in the webapp.
