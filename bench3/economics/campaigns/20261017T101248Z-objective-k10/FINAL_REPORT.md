# Ten-repetition objective benchmark — final results

Completed on 17 October 2026 at 14:44 in Asia/Jerusalem. The pilot is excluded.

## Result

- Base tasks: 1,965/2,100 passed (93.6%). The descriptive 95% Wilson interval is 92.4–94.5%.
- After the failure-only Aegis retry policy: 2,012/2,100 passed (95.8%). The descriptive interval is 94.9–96.6%.
- Enforced Aegis retries: 47/135 recovered a task (34.8%). The descriptive recovery interval is 27.3–43.2%.
- All 900 executed tool workflows passed before retry. The three GPT routes passed all 180 tool workflows.
- GPT-6.1 Sol passed 140/140 base tasks. GPT-6 Astra also passed 140/140. GPT-6 Luna passed 133/140.
- Base failures came from tiling (123), Catalan reasoning (9), and die expectation (3). No tool failure needed an Aegis retry.

## Integrity checks

- All 2,100 matrix cells exist exactly once. Each route/task/effort cell has ten new repetitions.
- All ten round proofs and report snapshots match the raw records.
- The independent audit replayed 2,235 grades, rechecked 135 signed journals, and replayed 405 method gates.
- Every failed base task has exactly one enforced retry. All passing retries have valid method closure.
- All pinned source and task hashes still match. The audit made no provider requests.
- See [the final audit](final_audit.json).

## One task: create an invoice, low effort

All routes passed 10/10 attempts. The 95% Wilson pass interval is 72.2–100% for each route. Each cost covers all model requests in the workflow. Costs are USD per 100,000 attempts; they also equal the observed cost per 100,000 successful tasks for this task.

| Model route | Cost / 100K tasks | 95% cost interval | Median seconds |
|---|---:|---:|---:|
| DeepSeek V4.1 Flash — LunaRoute | $3.51 | $3.04–$4.15 | 5.9 |
| GLM 5.3 — LunaRoute | $2.00 | $1.83–$2.21 | 13.2 |
| GLM 5.3 Flash — LunaRoute | $2.58 | $2.11–$3.05 | 10.3 |
| Muse Spark Open — LunaRoute | $4.09 | $3.77–$4.43 | 6.2 |
| DeepSeek V4.1 Flash — OpenRouter · price-first | $114.08 | $83.75–$144.71 | 9.3 |
| DeepSeek V4 Pro 0813 — OpenRouter · price-first | $176.36 | $75.44–$308.43 | 10.5 |
| GPT-6 Luna — OpenAI API | $58.49 | $52.56–$65.10 | 8.4 |
| DeepSeek V4.1 Flash — OpenRouter · default | $111.38 | $87.31–$139.67 | 10.3 |
| DeepSeek V4 Pro 0813 — OpenRouter · default | $129.09 | $54.17–$211.83 | 13.1 |
| GPT-6.1 Sol — OpenAI API | $985.36 | $982.68–$987.70 | 11.8 |
| Claude Haiku 5.5 — OpenRouter | $125.83 | $124.73–$127.41 | 7.1 |
| Claude Sonnet 5.5 — OpenRouter | $2,085.29 | $2,075.75–$2,096.58 | 8.2 |
| Claude Opus 5.5 — OpenRouter | $4,378.21 | $4,098.92–$4,663.83 | 13.9 |
| GPT-6 Astra — OpenAI API | $4,802.50 | $4,633.74–$4,925.20 | 11.8 |
| Claude Fable 5.1 — OpenRouter | $12,946.64 | $11,917.69–$13,882.30 | 20.5 |

LunaRoute costs use the supplied full-capacity allocation. They are not token invoices. The capacity assumption is the same for all LunaRoute models; this run does not measure account saturation or model-specific lane throughput.

## All route and effort settings

Each row combines an equal mix of seven fixed tasks, ten times each. It has 70 base tasks. Use this table as a declared workload mix, not as a general model rank. Base time is the median recorded model/workflow time. Local method audit time is not fully included.

| Model route | Effort | Base passes | 95% pass interval | After Aegis | Base cost / 100K attempts | Base cost / 100K successes | Policy cost / 100K successes | Base median seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek V4.1 Flash — LunaRoute | low | 62/70 | 79.0–94.1% | 64/70 | $1.82 | $2.05 | $2.32 | 4.8 |
| DeepSeek V4.1 Flash — LunaRoute | high | 60/70 | 75.7–92.1% | 61/70 | $1.82 | $2.12 | $2.53 | 5.0 |
| GLM 5.3 — LunaRoute | low | 65/70 | 84.3–96.9% | 68/70 | $1.04 | $1.12 | $1.18 | 6.4 |
| GLM 5.3 — LunaRoute | high | 65/70 | 84.3–96.9% | 68/70 | $1.29 | $1.39 | $1.50 | 11.8 |
| GLM 5.3 Flash — LunaRoute | low | 66/70 | 86.2–97.8% | 70/70 | $1.11 | $1.18 | $1.19 | 8.2 |
| GLM 5.3 Flash — LunaRoute | high | 67/70 | 88.1–98.5% | 70/70 | $1.21 | $1.26 | $1.27 | 11.5 |
| Muse Spark Open — LunaRoute | low | 70/70 | 94.8–100.0% | 70/70 | $2.16 | $2.16 | $2.16 | 5.5 |
| Muse Spark Open — LunaRoute | high | 60/70 | 75.7–92.1% | 66/70 | $2.71 | $3.17 | $3.24 | 9.2 |
| DeepSeek V4.1 Flash — OpenRouter · price-first | low | 61/70 | 77.3–93.1% | 62/70 | $107.29 | $123.12 | $158.60 | 18.1 |
| DeepSeek V4.1 Flash — OpenRouter · price-first | high | 59/70 | 74.0–91.0% | 61/70 | $119.92 | $142.27 | $178.65 | 19.3 |
| DeepSeek V4 Pro 0813 — OpenRouter · price-first | low | 59/70 | 74.0–91.0% | 60/70 | $347.34 | $412.10 | $438.95 | 15.6 |
| DeepSeek V4 Pro 0813 — OpenRouter · price-first | high | 52/70 | 63.0–83.1% | 60/70 | $437.16 | $588.48 | $557.80 | 20.5 |
| GPT-6 Luna — OpenAI API | low | 70/70 | 94.8–100.0% | 70/70 | $39.73 | $39.73 | $39.73 | 6.6 |
| GPT-6 Luna — OpenAI API | high | 63/70 | 80.8–95.1% | 67/70 | $64.20 | $71.33 | $88.38 | 6.9 |
| DeepSeek V4.1 Flash — OpenRouter · default | low | 70/70 | 94.8–100.0% | 70/70 | $91.97 | $91.97 | $91.97 | 11.2 |
| DeepSeek V4.1 Flash — OpenRouter · default | high | 64/70 | 82.5–96.0% | 66/70 | $101.78 | $111.32 | $125.98 | 10.6 |
| DeepSeek V4 Pro 0813 — OpenRouter · default | low | 60/70 | 75.7–92.1% | 60/70 | $527.51 | $615.43 | $648.37 | 13.3 |
| DeepSeek V4 Pro 0813 — OpenRouter · default | high | 59/70 | 74.0–91.0% | 60/70 | $733.44 | $870.18 | $899.14 | 18.8 |
| GPT-6.1 Sol — OpenAI API | low | 70/70 | 94.8–100.0% | 70/70 | $714.51 | $714.51 | $714.51 | 9.5 |
| GPT-6.1 Sol — OpenAI API | high | 70/70 | 94.8–100.0% | 70/70 | $914.65 | $914.65 | $914.65 | 12.9 |
| Claude Haiku 5.5 — OpenRouter | low | 69/70 | 92.3–99.7% | 70/70 | $88.53 | $89.81 | $90.27 | 5.7 |
| Claude Haiku 5.5 — OpenRouter | high | 66/70 | 86.2–97.8% | 69/70 | $110.07 | $116.74 | $122.95 | 6.9 |
| Claude Sonnet 5.5 — OpenRouter | low | 68/70 | 90.2–99.2% | 70/70 | $1,377.04 | $1,417.54 | $1,417.67 | 7.5 |
| Claude Sonnet 5.5 — OpenRouter | high | 70/70 | 94.8–100.0% | 70/70 | $1,475.57 | $1,475.57 | $1,475.57 | 8.0 |
| Claude Opus 5.5 — OpenRouter | low | 70/70 | 94.8–100.0% | 70/70 | $3,041.81 | $3,041.81 | $3,041.81 | 11.1 |
| Claude Opus 5.5 — OpenRouter | high | 70/70 | 94.8–100.0% | 70/70 | $3,648.11 | $3,648.11 | $3,648.11 | 13.1 |
| GPT-6 Astra — OpenAI API | low | 70/70 | 94.8–100.0% | 70/70 | $3,606.34 | $3,606.34 | $3,606.34 | 10.4 |
| GPT-6 Astra — OpenAI API | high | 70/70 | 94.8–100.0% | 70/70 | $4,855.03 | $4,855.03 | $4,855.03 | 13.3 |
| Claude Fable 5.1 — OpenRouter | low | 70/70 | 94.8–100.0% | 70/70 | $7,641.24 | $7,641.24 | $7,641.24 | 9.6 |
| Claude Fable 5.1 — OpenRouter | high | 70/70 | 94.8–100.0% | 70/70 | $8,504.64 | $8,504.64 | $8,504.64 | 11.2 |

The policy column includes the failed base task and its enforced retry. A recovered task remains one completed workflow, not two successes.

## Task-level details

- [Task and effort costs CSV](TASK_ECONOMICS.csv) has all 210 route/task/effort cells. It includes base cost per 100,000 attempts, cost per 100,000 successes, pass counts, pass intervals, and median time.
- [Full statistics JSON](summary.json) includes base and Aegis-policy values, task-cost intervals, and both effort settings.
- [Interactive local report](../../report.html) shows each task, route, effort, retry policy, and uncertainty.

## Recorded spend and limits

- Known cash cost for this campaign: $27.19. This is not a final provider invoice.
- LunaRoute allocated plan cost for this sample: $0.010213. This is separate from cash cost.
- One provider connection reset required a transport retry. Its interrupted request has no usage receipt. Any charge for that request is unknown.
- Tiling allowed 4,096 output tokens. Other reasoning tasks allowed 8,192. Tool workflows allowed 12 model requests, 32 tool calls, and 4,096 output tokens per request. Base and enforced retry limits matched.
- Pass intervals assume independent trials. Fixed prompts, provider caching, and route variation can violate that assumption. Pooled intervals describe this fixed task mix.
- Cost intervals use 1,000 bootstrap samples. They describe observed variation, not uncertainty in prices, the LunaRoute capacity assumption, or unknown interrupted-request charges.
- Ten repeats do not prove performance on unseen tasks. All tool tasks passed, so these tasks do not separate model quality after the harness fix.
- The study has no plain-retry control. A recovered task does not prove that Aegis caused the recovery.
- Publication is separate from this local audit. Check the GitHub Pages snapshot date and task count to see which result set is published.
