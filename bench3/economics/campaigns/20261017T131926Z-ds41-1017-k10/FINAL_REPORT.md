# DeepSeek V4.1 Flash 1017 — ten-repetition results

Completed on 17 October 2026 at 16:37 in Asia/Jerusalem (13:37 UTC).
The route is `ds41-1017-openrouter`. The pinned model is
`deepseek/deepseek-v4.1-flash-1017`.

## Result

- Base tasks: 128/140 passed (91.4%). The descriptive 95% Wilson interval is 85.6–95.0%.
- After one enforced Aegis retry per base failure: 133/140 passed (95.0%). The interval is 90.0–97.6%.
- Aegis recovered 5/12 failures (41.7%). The recovery interval is 19.3–68.0%.
- All 60 executed tool workflows passed before retry. All 12 failures came from tiling.
- Known cash cost, including all retries: $0.125693. No infrastructure errors were recorded.
- The retained baseline has 2,100 base observations. This extension adds 140. The comparison has 2,240, not 2,240 new model calls.

## Integrity checks

The independent audit checked all 140 matrix cells, ten round proofs,
152 grades, 12 signed evidence journals, and 36 method gates. Every failed
base task has exactly one enforced retry. Every passing retry has valid
method closure. The audit made no provider requests.

All pinned source and task hashes match. The retained baseline manifest
and final-audit hashes match the extension manifest. A second, read-only
baseline audit rechecked all 2,100 base records, 135 journals, and 405 gates.
It did not overwrite the original baseline audit.

See [the extension audit](final_audit.json) and
[the retained baseline report](../20261017T101248Z-objective-k10/FINAL_REPORT.md).

## Effort and measured costs

Each row has seven fixed tasks, ten times each. All costs are USD per
100,000 original tasks, except the columns marked “successes.” The Aegis
policy includes the failed base attempt and its enforced retry. A recovered
task counts as one success. “95% cost range” means a 1,000-draw bootstrap
interval from the recorded task costs.

| Effort | Base passes · 95% interval | After Aegis · 95% interval | Base cost | Base 95% cost range | Aegis cost | Aegis 95% cost range | Base / 100K successes | Aegis / 100K successes | Base median seconds |
|---|---|---|---:|---|---:|---|---:|---:|---:|
| low | 64/70 · 82.5–96.0% | 67/70 · 88.1–98.5% | $69.31 | $55.85–$82.77 | $86.39 | $61.73–$112.32 | $75.81 | $90.25 | 9.9 |
| high | 64/70 · 82.5–96.0% | 66/70 · 86.2–97.8% | $74.62 | $61.95–$88.13 | $93.18 | $69.01–$120.29 | $81.62 | $98.82 | 10.9 |

Low effort recovered 3/6 failures. High effort recovered 2/6. These are
small samples. They do not establish an effort advantage.

## Task and effort costs

Each row has ten base attempts. All non-tiling rows passed 10/10 before
retry. Their 95% Wilson pass interval is 72.2–100%. Tiling passed 4/10 at
each effort; its base interval is 16.8–68.7%. After Aegis, tiling passed
7/10 at low effort (39.7–89.2%) and 6/10 at high effort (31.3–83.2%).

| Task | Effort | Base passes | After Aegis | Base cost / 100K | Base 95% cost range | Aegis cost / 100K | Base median seconds |
|---|---|---:|---:|---:|---|---:|---:|
| Tiling | low | 4/10 | 7/10 | $193.65 | $170.37–$213.23 | $313.20 | 42.2 |
| Tiling | high | 4/10 | 6/10 | $186.50 | $156.60–$208.30 | $316.39 | 42.2 |
| Expected flips | low | 10/10 | 10/10 | $31.41 | $28.76–$34.08 | $31.41 | 5.2 |
| Expected flips | high | 10/10 | 10/10 | $28.95 | $26.69–$31.46 | $28.95 | 9.2 |
| Die expectation | low | 10/10 | 10/10 | $28.40 | $26.17–$30.53 | $28.40 | 4.7 |
| Die expectation | high | 10/10 | 10/10 | $31.21 | $27.71–$35.29 | $31.21 | 14.7 |
| Catalan count | low | 10/10 | 10/10 | $67.60 | $52.72–$85.02 | $67.60 | 27.2 |
| Catalan count | high | 10/10 | 10/10 | $99.68 | $80.67–$124.77 | $99.68 | 16.8 |
| Invoice workflow | low | 10/10 | 10/10 | $70.40 | $61.32–$80.27 | $70.40 | 10.5 |
| Invoice workflow | high | 10/10 | 10/10 | $76.27 | $63.23–$90.64 | $76.27 | 10.2 |
| Support workflow | low | 10/10 | 10/10 | $30.96 | $28.83–$33.06 | $30.96 | 5.7 |
| Support workflow | high | 10/10 | 10/10 | $30.72 | $28.28–$33.24 | $30.72 | 5.5 |
| Inventory workflow | low | 10/10 | 10/10 | $62.74 | $59.38–$65.67 | $62.74 | 7.6 |
| Inventory workflow | high | 10/10 | 10/10 | $69.02 | $64.26–$73.05 | $69.02 | 8.6 |

The Aegis tiling policy had median model time of 75.6 seconds at low
effort and 86.1 seconds at high effort. Local evidence checks and method
audit time are not fully included in these latency values.

## Comparison with the older cohort

These routes used the same task and output-limit contract. They ran
earlier. Default provider selection, caching, and service conditions can
differ. This is not a concurrent paired comparison or a significance test.

| Route | Effort | Base passes | After Aegis | Base cost / 100K attempts | Aegis cost / 100K successes | Base median seconds |
|---|---|---:|---:|---:|---:|---:|
| DeepSeek V4.1 Flash 1017 · OpenRouter | low | 64/70 | 67/70 | $69.31 | $90.25 | 9.9 |
| DeepSeek V4.1 Flash 1017 · OpenRouter | high | 64/70 | 66/70 | $74.62 | $98.82 | 10.9 |
| Earlier DeepSeek V4.1 Flash · OpenRouter default | low | 70/70 | 70/70 | $91.97 | $91.97 | 11.2 |
| Earlier DeepSeek V4.1 Flash · OpenRouter default | high | 64/70 | 66/70 | $101.78 | $125.98 | 10.6 |
| DeepSeek V4.1 Flash · LunaRoute | low | 62/70 | 64/70 | $1.82 | $2.32 | 4.8 |
| DeepSeek V4.1 Flash · LunaRoute | high | 60/70 | 61/70 | $1.82 | $2.53 | 5.0 |
| GPT-6.1 Sol · OpenAI API | low | 70/70 | 70/70 | $714.51 | $714.51 | 9.5 |
| GPT-6.1 Sol · OpenAI API | high | 70/70 | 70/70 | $914.65 | $914.65 | 12.9 |

The pinned 1017 route has lower observed attempt cost than the earlier
OpenRouter default route. It does not improve the observed base pass count.
The data does not establish general model quality or a cause for the cost
difference. GPT-6.1 Sol remains 140/140 on the objective base tasks.

## Aegis-first hybrid and greedy cost ladder

The report now separates measured base-only and Aegis-only policies from
estimated model upgrades. Costs below include all failed base attempts and
all recorded Aegis retries. They use the same equal mix of seven tasks.

`Aegis-first hybrid = mean base-plus-Aegis cost + remaining failure ratio × fallback cost`

At each ladder level, try the base workflow. On failure, use one enforced
Aegis retry with that model. Upgrade only if the retry also fails. Choose
the next model by the lowest cost/pass ratio among models with a higher
observed after-Aegis pass ratio for that task and effort. Remove levels
that do not reduce estimated cost. Latency is not in the score.

The final fallback must pass all 140 objective base tasks. Four routes meet
that rule: GPT-6.1 Sol, Claude Opus 5.5, GPT-6 Astra, and Claude Fable 5.1.
Sol has the lowest measured task cost among those routes for these tasks.
Intermediate levels need complete task results and all required retries;
they do not need a perfect score across the full benchmark.

| Starting route | Effort | Measured Aegis-only cost / 100K attempts | Estimated Aegis → fallback | Estimated Aegis cost ladder |
|---|---|---:|---:|---:|
| DeepSeek V4.1 Flash · LunaRoute | low | $2.12 | $90.87 | $2.19 |
| DeepSeek V4.1 Flash · LunaRoute | high | $2.20 | $222.78 | $2.34 |
| GLM 5.3 Flash · LunaRoute | low | $1.19 | $1.19 | $1.19 |
| GLM 5.3 Flash · LunaRoute | high | $1.27 | $1.27 | $1.27 |
| DeepSeek V4.1 Flash 1017 · OpenRouter | low | $86.39 | $130.76 | $86.42 |
| DeepSeek V4.1 Flash 1017 · OpenRouter | high | $93.18 | $191.21 | $93.24 |

GLM Flash recovered all seven of its base failures with Aegis. Its
estimated upgrade cost is therefore zero in this sample. That is not a
guarantee of zero future failures. The estimated high-effort tiling ladder
from LunaRoute DeepSeek is DeepSeek → GLM Flash → Sol. Each non-final
level includes Aegis. Sol remains a final guard even when its estimated
reach is zero.

No linked model ladder was run. The estimate uses marginal pass rates,
not observed pass rates on upstream failures. Models can fail on the same
cases. Stage costs on harder upstream failures can differ from the sample
mean. The same small sample selects and scores the ladder. Actual costs
can therefore be higher. The heuristic is not proven globally optimal.
No combined observed pass rate, policy confidence interval, or statistical
significance is claimed.

The CSV download also keeps the original weighted formula
`p × base cost + (1 − p) × fallback cost`. It omits failed cheap attempts
and all Aegis retries. It is not the Aegis-first hybrid bill shown above.

## Data and limits

- [Task economics CSV](TASK_ECONOMICS.csv) has all 224 route/task/effort cells across both cohorts.
- [Full statistics JSON](summary.json) keeps base and Aegis-policy results, pass intervals, and task-cost intervals.
- [Interactive report](https://eranshir.github.io/bench3/economics/) has policy switches, ladder paths, and a CSV download for all cost policies.
- Tiling allows 4,096 output tokens. Other reasoning tasks allow 8,192. Tool workflows allow 12 model requests, 32 tool calls, and 4,096 output tokens per request. Base and Aegis retry limits match.
- OpenRouter costs use returned charges and the configured 5.5% credit fee. They are recorded sample costs, not a final provider invoice.
- LunaRoute costs use the supplied $500 plan at full capacity: 4 billion tokens per day for 30 days. The run does not measure model-specific lane throughput.
- Pass intervals assume independent trials. Repeated prompts, caching, and route variation can violate this assumption. Fixed-task results do not establish performance on unseen tasks.
- Cost intervals describe recorded variation. They do not cover future prices, capacity-assumption errors, or unknown interrupted-request charges in the older cohort.
- The study has no plain-retry control. A recovery does not show that Aegis caused the recovery.
