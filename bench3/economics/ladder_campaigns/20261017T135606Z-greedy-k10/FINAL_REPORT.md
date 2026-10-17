# Measured Aegis-first cost ladders — ten fresh repetitions

Completed on 17 October 2026 at 18:38 in Asia/Jerusalem (15:38 UTC).

## Result

All **2,240 fresh linked workflows passed**. The descriptive 95% Wilson pass interval is 99.83–100%. This fixed-task result is not proof of perfect reliability.

The matrix has 16 starting routes, seven tasks, low and high effort, and ten fresh repetitions per setting. The earlier 2,240 single-route observations selected the plans. They remain separate and are not counted as fresh workflows.

The run executed 2,334 base attempts and 184 fully enforced Aegis retries. Aegis recovered 90/184 failed attempts (48.9%). The descriptive recovery interval is 41.8–56.1%. The ladders made 94 model upgrades across 84 original workflows. No call followed an objective pass.

At the first model, 2,090/2,240 workflows passed before retry. Aegis recovered 66/150 first-model failures. The other 84 workflows moved to another model. Later levels had 34 retries and 24 recoveries.

Known cash cost was **$30.281771**. LunaRoute capacity allocation added **$0.011362**. One timeout has no usage receipt. Its charge remains unknown, not zero. Thus, the complete bill is not known.

## Policy and cost definitions

Every reached model gets the original task and fresh tool state. Run one base attempt. On an objective failure, run exactly one fully enforced Aegis retry with that model. Upgrade only if both attempts fail and the method checks and signed journal verify. Stop at the first objective pass. If the final model and retry fail, record a failed workflow.

Aegis includes plan and child contracts, the full instruction payload, objective checks, completion and closure checks, and a signed evidence journal. This is a benchmark-native method adapter. It does not claim native Codex or Claude hook equivalence.

The greedy plans were frozen before this run. The selection score optimizes expected cost, not latency. A terminal fallback must pass all 140 training base tasks across all seven tasks, both efforts, and ten repetitions. Qualified training routes were Sol, Opus, Astra, and Fable. Sol had the lowest task cost among them for these tasks. A qualified starting route can itself be the final level.

| Report view | Evidence | Cost counted |
|---|---|---|
| Base only | Earlier single-route observations | Every base attempt, including failures |
| Aegis only | Earlier base and retry observations | Base plus every failure-only enforced retry |
| Aegis then fallback | Frozen estimate | Aegis-only cost plus remaining failure ratio times qualified fallback cost |
| Estimated Aegis cost ladder | Frozen estimate | Estimated reach times full base-plus-retry cost at each level |
| Measured ladder | This fresh linked run | Actual sum of every reached base attempt and enforced retry |

The original weighted formula, `p × base cost + (1 − p) × fallback cost`, remains in the training CSV download. It omits failed cheap attempts. It is not an actual cheap-first bill.

Measured cost per 100,000 original workflows is `100000 × sum(all reached attempt costs) / original workflow count`. Cost per 100,000 successes uses successful original workflows as the denominator. Every workflow passed here, so the two costs are equal. A retry or upgrade is not a new original workflow.

Token-billed routes use recorded direct cash charges or OpenRouter charges with the configured 5.5% credit fee. LunaRoute uses the supplied full-capacity rule: $500 per 30 days and 4 billion tokens per day. This is $0.004167 per million tokens. This run measures task token use, not model-specific lane throughput. Capacity allocation is not a new per-request cash charge.

## Main findings

GLM 5.3 through LunaRoute had the lowest observed equal-task mean at both efforts: $1.10 at low effort and $1.51 at high effort per 100,000 original workflows. Each setting passed 70/70. This does not establish a general model rank.

Rare upgrades had a large cost effect. At high effort, the GLM Flash starting route needed one Sol upgrade. Its measured equal-task mean was $26.83 per 100,000 workflows, compared with the frozen $1.27 estimate. The bootstrap interval was $1.15–$78.06. In high-effort tiling, GLM Flash passed 5/10 base attempts and recovered 4/5 with Aegis. Sol passed the remaining workflow. Sol contributed $178.48 of the $179.93 cost per 100,000 tiling workflows.

The high-effort LunaRoute DeepSeek ladder cost $53.57 per 100,000 workflows, compared with the frozen $2.34 estimate. Its interval was $2.14–$130.63. In high-effort tiling, DeepSeek passed 0/10 after Aegis. GLM Flash resolved 8/10 reached workflows. Sol resolved the other two. These are measured conditional results on this path, not general model pass rates.

GPT-6.1 Sol passed all 140 first-model base tasks in this fresh run. It needed no Aegis retry when it was the starting route. Its mean cost was $710.59 at low effort and $917.56 at high effort per 100,000 workflows. Its median wall time was 9.4 and 12.9 seconds. The proper tool loop does not show the earlier GPT disadvantage on these small objective tasks.

## Route and effort results

Each row has an equal mix of seven fixed tasks, ten times each. All 32 settings passed 70/70. Each has a descriptive 95% Wilson pass interval of 94.8–100%. Costs are USD per 100,000 original workflows. The 95% cost interval uses 1,000 percentile bootstrap resamples.

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Retries | Upgrades | Median wall seconds | Median active seconds |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| DeepSeek V4.1 Flash · LunaRoute | low | 70/70 | $18.47 | $1.77–$51.38 | $2.19 | 10 | 8 | 5.3 | 5.2 |
| DeepSeek V4.1 Flash · LunaRoute | high | 70/70 | $53.57 | $2.14–$130.63 | $2.34 | 16 | 12 | 5.3 | 5.3 |
| GLM 5.3 · LunaRoute | low | 70/70 | $1.10 | $0.89–$1.30 | $1.17 | 2 | 0 | 7.7 | 7.6 |
| GLM 5.3 · LunaRoute | high | 70/70 | $1.51 | $1.24–$1.82 | $1.49 | 6 | 2 | 10.5 | 10.5 |
| GLM 5.3 Flash · LunaRoute | low | 70/70 | $1.24 | $0.91–$1.66 | $1.19 | 3 | 0 | 8.0 | 8.0 |
| GLM 5.3 Flash · LunaRoute | high | 70/70 | $26.83 | $1.15–$78.06 | $1.27 | 6 | 1 | 12.8 | 12.7 |
| Muse Spark Open · LunaRoute | low | 70/70 | $2.16 | $1.73–$2.65 | $2.16 | 0 | 0 | 5.7 | 5.6 |
| Muse Spark Open · LunaRoute | high | 70/70 | $3.22 | $2.72–$3.73 | $3.11 | 11 | 5 | 9.1 | 9.1 |
| DeepSeek V4.1 Flash · OpenRouter · price-first | low | 70/70 | $127.61 | $88.14–$176.68 | $140.58 | 8 | 3 | 9.2 | 9.2 |
| DeepSeek V4.1 Flash · OpenRouter · price-first | high | 70/70 | $138.02 | $106.97–$173.27 | $155.82 | 11 | 4 | 9.5 | 9.5 |
| DeepSeek V4 Pro 0813 · OpenRouter · price-first | low | 70/70 | $1694.20 | $1271.89–$2155.08 | $376.37 | 17 | 11 | 14.1 | 14.1 |
| DeepSeek V4 Pro 0813 · OpenRouter · price-first | high | 70/70 | $2420.35 | $1800.84–$3132.02 | $478.27 | 24 | 12 | 19.1 | 19.1 |
| GPT-6 Luna · OpenAI API | low | 70/70 | $42.69 | $36.35–$49.23 | $39.73 | 2 | 0 | 6.6 | 6.6 |
| GPT-6 Luna · OpenAI API | high | 70/70 | $105.42 | $59.96–$175.81 | $84.64 | 7 | 4 | 7.8 | 7.7 |
| DeepSeek V4.1 Flash · OpenRouter · default | low | 70/70 | $119.63 | $86.77–$166.91 | $91.97 | 2 | 1 | 8.9 | 8.8 |
| DeepSeek V4.1 Flash · OpenRouter · default | high | 70/70 | $135.22 | $107.06–$164.76 | $118.84 | 8 | 3 | 9.2 | 9.2 |
| DeepSeek V4.1 Flash 1017 · OpenRouter · pinned 1017 | low | 70/70 | $132.86 | $91.79–$184.66 | $86.42 | 12 | 6 | 15.6 | 15.6 |
| DeepSeek V4.1 Flash 1017 · OpenRouter · pinned 1017 | high | 70/70 | $102.78 | $79.36–$130.19 | $93.24 | 6 | 2 | 17.9 | 17.9 |
| DeepSeek V4 Pro 0813 · OpenRouter · default | low | 70/70 | $1075.29 | $785.51–$1355.62 | $555.88 | 15 | 10 | 14.0 | 13.9 |
| DeepSeek V4 Pro 0813 · OpenRouter · default | high | 70/70 | $1481.73 | $1058.13–$1904.71 | $770.85 | 13 | 9 | 16.1 | 16.0 |
| GPT-6.1 Sol · OpenAI API | low | 70/70 | $710.59 | $632.50–$786.60 | $714.51 | 0 | 0 | 9.4 | 9.3 |
| GPT-6.1 Sol · OpenAI API | high | 70/70 | $917.56 | $818.22–$1024.65 | $914.65 | 0 | 0 | 12.9 | 12.9 |
| Claude Haiku 5.5 · OpenRouter | low | 70/70 | $85.72 | $73.55–$98.43 | $90.27 | 0 | 0 | 5.8 | 5.8 |
| Claude Haiku 5.5 · OpenRouter | high | 70/70 | $119.61 | $101.42–$140.11 | $121.20 | 3 | 1 | 6.4 | 6.4 |
| Claude Sonnet 5.5 · OpenRouter | low | 70/70 | $1421.93 | $1213.31–$1623.60 | $1417.67 | 2 | 0 | 7.9 | 7.8 |
| Claude Sonnet 5.5 · OpenRouter | high | 70/70 | $1468.82 | $1256.77–$1665.30 | $1475.57 | 0 | 0 | 8.1 | 8.0 |
| Claude Opus 5.5 · OpenRouter | low | 70/70 | $3057.14 | $2725.23–$3411.78 | $3041.81 | 0 | 0 | 10.9 | 10.9 |
| Claude Opus 5.5 · OpenRouter | high | 70/70 | $3628.87 | $3166.75–$4052.88 | $3648.11 | 0 | 0 | 12.8 | 12.8 |
| GPT-6 Astra · OpenAI API | low | 70/70 | $3548.05 | $3167.43–$3946.62 | $3606.34 | 0 | 0 | 10.2 | 10.2 |
| GPT-6 Astra · OpenAI API | high | 70/70 | $4715.00 | $4254.32–$5192.94 | $4855.03 | 0 | 0 | 13.0 | 12.9 |
| Claude Fable 5.1 · OpenRouter | low | 70/70 | $7543.99 | $6342.72–$8759.33 | $7641.24 | 0 | 0 | 10.0 | 9.9 |
| Claude Fable 5.1 · OpenRouter | high | 70/70 | $8374.73 | $7169.76–$9578.10 | $8504.64 | 0 | 0 | 11.6 | 11.6 |

## Time

Active time is the sum of saved attempt durations across all reached models and retries. Tool-loop time includes model waits and local tool execution. It is not pure GPU or network time.

Full wall time runs from workflow start to finish. It includes local method checks and resume delays. Queue time before workflow start is excluded. The greedy score did not use time.

Median wall time across all original workflows was 9.3 seconds. Median active time was 9.2 seconds. Low effort had median wall time 8.4 seconds; high effort had 10.4 seconds. These pooled medians describe this fixed task and route mix. The tables give separate task and configuration medians. A mean of medians is not used.

One DeepSeek 1017 support workflow includes a human approval wait. Its full wall time was 552.5 seconds. Its active time excludes the approval wait. The wait remains in the wall sample.

## Independent audits and approved recovery

The main final audit passed. It verified all 2,240 unique workflows, 2,518 attempt grades, ten round proofs, reached paths, retry parents, stop rules, frozen source hashes, and stage costs.

The separate strict journal audit passed. It checked 184 nonempty signed journals with 368 signed entries and 552 method checks at the actual run roots. Each journal matched its saved head, segment, journal identity, and public-key identity.

An older audit helper can use a reasoning adapter's `.am` directory instead of its parent run directory. The adapter wrote and verified the correct journal during the run. The extra strict audit uses the actual evidence-state path and rejects empty journals. No source pin or task outcome changed.

The retained 2,100-task cohort and 140-task extension both passed a new read-only audit. Their original manifest and final audit hashes remain unchanged. Their additional strict journal audits checked 135 and 12 nonempty journals.

The approved recovery concerned only `ds41-1017-openrouter / tool-use/t2_toolselect / high / repetition 7`. The fourth provider request timed out after three completed model and tool results. The helper replayed those results locally. It sent none of the completed requests again. Two new requests completed the workflow. The timeout consumed one request slot: six actual requests in total, under the unchanged limit of twelve.

Known cost of that workflow is $0.00074603692. Its timeout charge is unknown. Original raw timeout and prefix artifacts remain intact. The separate helper hash is disclosed in the recovery audit. All original source pins match.

The run recorded 6,347 model requests, with 6,346 returned usage receipts and one missing receipt. These are model requests, not original workflows. The audits made no provider requests.

All 47 Python tests and all three JavaScript test programs passed. The report interaction test uses a document model stub. It is not a browser layout or visual test.

## Comparison with the frozen estimates

Training had 2,093/2,240 base passes and 2,145/2,240 passes after Aegis without a linked upgrade. The fresh run had 2,090/2,240 first-model base passes and 2,156/2,240 first-model passes after Aegis. Actual linked upgrades resolved the remaining 84 workflows.

The runs occurred at different times. They are not a randomized paired policy comparison. Cache state, default routing, and provider conditions can differ. The frozen estimates use marginal pass rates from separate model runs. The fresh data measures conditional reach and costs on actual upstream failures. No significance test or causal Aegis claim is made.

## Task and effort results

Every row has ten original workflows and ten passes. Its descriptive 95% Wilson pass interval is 72.2–100%. Both cost columns use 100,000 original workflows. Cost per 100,000 successes is equal here. Cost intervals do not include unknown charges.

### Long tiling proof (`reasoning/r1_tiling`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $118.80 | $3.48–$348.41 | $4.36 | 62.2 | 61.9 | 10 / 8 |
| `glm53-lunaroute` | low | 10/10 | $0.83 | $0.49–$1.28 | $1.40 | 8.7 | 8.6 | 2 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $0.71 | $0.32–$1.24 | $0.88 | 16.1 | 16.1 | 2 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $0.96 | $0.82–$1.10 | $0.98 | 9.0 | 9.0 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $397.10 | $238.87–$639.90 | $489.00 | 70.3 | 70.2 | 8 / 3 |
| `dspro-openrouter-floor` | low | 10/10 | $3766.49 | $2463.81–$5174.76 | $1037.61 | 141.9 | 141.4 | 16 / 11 |
| `gpt6-luna-direct` | low | 10/10 | $66.53 | $57.18–$82.30 | $64.71 | 13.1 | 13.0 | 1 / 0 |
| `ds41-openrouter` | low | 10/10 | $274.45 | $124.64–$539.04 | $130.00 | 27.3 | 27.3 | 2 / 1 |
| `ds41-1017-openrouter` | low | 10/10 | $560.06 | $435.02–$779.95 | $313.46 | 122.6 | 122.1 | 11 / 6 |
| `dspro-openrouter` | low | 10/10 | $2788.52 | $2096.89–$3978.56 | $1481.60 | 146.1 | 145.7 | 15 / 10 |
| `gpt61-sol-direct` | low | 10/10 | $1030.30 | $994.69–$1067.80 | $1035.50 | 25.0 | 24.9 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $99.00 | $90.87–$107.32 | $128.92 | 8.6 | 8.5 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $1350.97 | $1000.11–$1770.05 | $1356.62 | 8.3 | 8.3 | 2 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $2509.21 | $2397.78–$2617.89 | $2523.77 | 11.4 | 11.4 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $5269.00 | $5072.41–$5487.51 | $5412.00 | 18.5 | 18.5 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $4879.38 | $4375.03–$5272.97 | $4825.57 | 10.7 | 10.7 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $363.67 | $5.68–$897.82 | $5.41 | 93.2 | 92.9 | 15 / 12 |
| `glm53-lunaroute` | high | 10/10 | $2.51 | $1.40–$3.79 | $2.49 | 34.1 | 33.9 | 6 / 2 |
| `glm53-flash-lunaroute` | high | 10/10 | $179.93 | $0.98–$537.47 | $1.08 | 38.9 | 38.6 | 5 / 1 |
| `muse-spark-open-lunaroute` | high | 10/10 | $5.19 | $4.56–$6.01 | $4.59 | 48.6 | 48.4 | 11 / 5 |
| `ds41-openrouter-floor` | high | 10/10 | $409.55 | $368.45–$454.37 | $505.10 | 82.5 | 82.3 | 11 / 4 |
| `dspro-openrouter-floor` | high | 10/10 | $4575.47 | $3655.87–$5812.86 | $1033.18 | 171.1 | 170.7 | 15 / 12 |
| `gpt6-luna-direct` | high | 10/10 | $489.83 | $250.18–$870.10 | $345.25 | 78.5 | 78.3 | 7 / 4 |
| `ds41-openrouter` | high | 10/10 | $253.68 | $173.91–$333.62 | $281.78 | 44.5 | 44.4 | 6 / 3 |
| `ds41-1017-openrouter` | high | 10/10 | $310.06 | $217.33–$402.05 | $316.83 | 127.9 | 127.8 | 6 / 2 |
| `dspro-openrouter` | high | 10/10 | $2757.17 | $2253.34–$3751.94 | $1484.58 | 142.6 | 142.3 | 13 / 9 |
| `gpt61-sol-direct` | high | 10/10 | $1770.20 | $1691.99–$1845.64 | $1715.60 | 32.7 | 32.7 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $250.61 | $174.80–$333.91 | $258.14 | 16.7 | 16.6 | 3 / 1 |
| `claude-sonnet55-openrouter` | high | 10/10 | $1375.61 | $1316.22–$1450.73 | $1336.47 | 9.2 | 9.2 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $2896.82 | $2745.10–$3039.91 | $3005.06 | 12.9 | 12.8 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $8491.50 | $8192.00–$8785.54 | $8590.00 | 29.2 | 29.2 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $7670.38 | $6984.06–$8403.33 | $7162.92 | 16.0 | 15.9 | 0 / 0 |

### Expected flips (`reasoning/r2_expectedflips`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $0.25 | $0.23–$0.26 | $0.24 | 2.8 | 2.7 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $0.21 | $0.20–$0.23 | $0.20 | 12.1 | 12.0 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $0.16 | $0.15–$0.18 | $0.16 | 4.7 | 4.7 | 0 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $0.43 | $0.39–$0.48 | $0.42 | 3.0 | 3.0 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $32.20 | $30.39–$34.54 | $39.72 | 4.6 | 4.6 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $1029.49 | $858.57–$1200.91 | $139.77 | 16.4 | 16.3 | 0 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $16.96 | $16.25–$17.59 | $15.96 | 4.0 | 3.9 | 0 / 0 |
| `ds41-openrouter` | low | 10/10 | $52.29 | $46.02–$60.20 | $42.24 | 2.8 | 2.7 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $33.59 | $29.10–$39.10 | $31.41 | 7.1 | 7.1 | 1 / 0 |
| `dspro-openrouter` | low | 10/10 | $305.60 | $162.77–$447.20 | $301.07 | 15.0 | 15.0 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $278.10 | $267.80–$291.00 | $292.50 | 6.5 | 6.5 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $25.05 | $24.11–$25.88 | $25.00 | 2.7 | 2.6 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $460.09 | $445.63–$474.65 | $456.50 | 3.4 | 3.4 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $1187.30 | $1086.85–$1283.96 | $1215.15 | 6.8 | 6.8 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $1339.50 | $1272.50–$1425.00 | $1338.50 | 5.0 | 5.0 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $2217.08 | $2143.76–$2319.43 | $2191.76 | 6.5 | 6.5 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $0.26 | $0.25–$0.27 | $0.27 | 2.8 | 2.8 | 0 / 0 |
| `glm53-lunaroute` | high | 10/10 | $0.28 | $0.26–$0.30 | $0.30 | 8.4 | 8.4 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $0.27 | $0.26–$0.28 | $0.29 | 6.8 | 6.7 | 0 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $0.75 | $0.68–$0.83 | $0.71 | 6.9 | 6.8 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $30.44 | $25.92–$33.41 | $40.84 | 5.2 | 5.1 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $1069.96 | $761.14–$1333.44 | $222.89 | 22.6 | 22.6 | 0 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $17.86 | $17.01–$18.82 | $18.18 | 4.1 | 4.1 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $53.12 | $48.29–$59.53 | $44.73 | 3.0 | 2.9 | 0 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $31.51 | $29.17–$33.88 | $28.95 | 13.9 | 13.9 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $607.07 | $330.33–$930.06 | $477.47 | 16.0 | 15.9 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $335.60 | $326.10–$345.80 | $338.10 | 7.6 | 7.5 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $42.09 | $40.75–$43.59 | $41.90 | 3.7 | 3.7 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $493.11 | $472.63–$513.05 | $499.65 | 3.6 | 3.6 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $1743.91 | $1656.34–$1829.59 | $1787.38 | 8.0 | 8.0 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $1928.00 | $1876.00–$1985.01 | $1826.00 | 7.2 | 7.2 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $2346.85 | $2264.53–$2433.91 | $2316.25 | 7.0 | 7.0 | 0 / 0 |

### Die expectation (`reasoning/r3_die_expected`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $0.24 | $0.22–$0.27 | $0.22 | 2.7 | 2.6 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $0.23 | $0.20–$0.25 | $0.22 | 3.6 | 3.5 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $0.20 | $0.17–$0.23 | $0.19 | 7.0 | 6.9 | 0 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $0.40 | $0.37–$0.44 | $0.41 | 3.6 | 3.5 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $28.61 | $26.55–$30.71 | $41.60 | 4.0 | 4.0 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $801.92 | $691.71–$924.74 | $48.47 | 15.5 | 15.4 | 0 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $15.85 | $15.05–$16.57 | $14.95 | 3.8 | 3.7 | 0 / 0 |
| `ds41-openrouter` | low | 10/10 | $57.15 | $52.21–$62.20 | $59.59 | 1.7 | 1.6 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $30.19 | $24.29–$36.01 | $28.40 | 6.3 | 6.2 | 0 / 0 |
| `dspro-openrouter` | low | 10/10 | $352.18 | $226.22–$466.72 | $129.00 | 17.9 | 17.8 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $398.60 | $387.70–$414.71 | $396.20 | 7.1 | 7.1 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $31.99 | $28.78–$35.32 | $32.80 | 3.3 | 3.3 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $426.22 | $418.62–$435.40 | $431.60 | 3.1 | 3.1 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $1573.85 | $1449.14–$1704.27 | $1551.27 | 7.5 | 7.5 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $1875.00 | $1815.50–$1942.50 | $1866.00 | 6.4 | 6.4 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $2551.52 | $2410.57–$2707.14 | $2658.07 | 7.7 | 7.6 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $0.36 | $0.23–$0.61 | $0.26 | 2.5 | 2.5 | 1 / 0 |
| `glm53-lunaroute` | high | 10/10 | $0.31 | $0.29–$0.33 | $0.34 | 4.4 | 4.4 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $0.44 | $0.29–$0.71 | $0.43 | 14.2 | 14.2 | 1 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $0.83 | $0.76–$0.91 | $0.82 | 7.9 | 7.9 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $31.13 | $29.70–$32.54 | $48.82 | 4.9 | 4.9 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $1364.79 | $864.24–$1903.18 | $147.76 | 23.1 | 23.1 | 0 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $17.63 | $16.39–$18.87 | $18.77 | 4.3 | 4.2 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $132.49 | $63.19–$237.64 | $63.30 | 1.9 | 1.9 | 2 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $32.62 | $28.70–$36.87 | $31.21 | 8.1 | 8.1 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $306.55 | $224.23–$391.07 | $360.09 | 17.2 | 17.2 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $537.40 | $513.50–$563.41 | $566.90 | 11.3 | 11.3 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $42.15 | $40.20–$44.65 | $44.68 | 3.9 | 3.9 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $455.44 | $443.21–$468.95 | $466.63 | 3.3 | 3.2 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $1850.89 | $1788.85–$1912.95 | $1743.28 | 8.2 | 8.1 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $2883.00 | $2783.49–$2985.54 | $2913.00 | 9.2 | 9.2 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $3173.97 | $2897.44–$3433.00 | $3024.16 | 8.2 | 8.2 | 0 / 0 |

### Catalan count (`reasoning/r4_catalan`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $0.67 | $0.56–$0.79 | $0.73 | 9.1 | 9.0 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $0.25 | $0.22–$0.29 | $0.26 | 12.7 | 12.7 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $0.19 | $0.17–$0.21 | $0.20 | 4.8 | 4.7 | 0 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $0.46 | $0.40–$0.53 | $0.45 | 5.3 | 5.3 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $59.16 | $53.79–$65.36 | $64.82 | 14.3 | 14.3 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $4471.44 | $3363.42–$5634.47 | $665.16 | 76.0 | 75.9 | 1 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $18.43 | $16.97–$20.19 | $20.27 | 4.3 | 4.3 | 0 / 0 |
| `ds41-openrouter` | low | 10/10 | $80.56 | $52.77–$117.52 | $59.69 | 15.1 | 15.1 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $77.07 | $67.14–$86.56 | $67.60 | 18.5 | 18.5 | 0 / 0 |
| `dspro-openrouter` | low | 10/10 | $2453.43 | $1892.56–$3040.42 | $1232.37 | 25.9 | 25.8 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $382.80 | $360.20–$409.40 | $383.10 | 8.1 | 8.1 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $34.45 | $31.68–$37.38 | $32.71 | 3.6 | 3.6 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $667.39 | $612.74–$732.91 | $627.94 | 4.8 | 4.7 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $1770.92 | $1590.30–$1974.16 | $1671.75 | 7.9 | 7.9 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $2048.00 | $1864.97–$2215.50 | $2180.00 | 8.3 | 8.3 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $3023.10 | $2856.93–$3219.39 | $3134.93 | 7.3 | 7.3 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $1.01 | $0.82–$1.22 | $0.96 | 15.7 | 15.7 | 0 / 0 |
| `glm53-lunaroute` | high | 10/10 | $0.62 | $0.48–$0.77 | $0.43 | 17.5 | 17.4 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $0.39 | $0.36–$0.42 | $0.34 | 10.0 | 10.0 | 0 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $1.25 | $1.06–$1.44 | $1.35 | 10.7 | 10.7 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $93.34 | $69.53–$113.24 | $129.74 | 23.6 | 23.5 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $7971.43 | $6612.74–$9012.26 | $1065.55 | 150.5 | 150.3 | 9 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $36.05 | $29.85–$42.48 | $37.79 | 7.6 | 7.6 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $99.53 | $76.76–$124.96 | $75.19 | 19.8 | 19.8 | 0 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $97.70 | $79.59–$116.86 | $99.68 | 28.5 | 28.4 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $4927.96 | $4077.18–$5833.93 | $2098.90 | 64.2 | 64.1 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $780.00 | $751.18–$812.91 | $694.20 | 16.3 | 16.3 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $74.29 | $65.14–$85.09 | $78.50 | 6.1 | 6.1 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $672.77 | $632.68–$709.81 | $662.86 | 4.9 | 4.9 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $2115.49 | $1857.21–$2389.45 | $2231.75 | 9.2 | 9.2 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $3925.00 | $3686.80–$4149.01 | $4113.00 | 14.4 | 14.3 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $4078.63 | $3681.42–$4499.59 | $3680.37 | 9.2 | 9.2 | 0 / 0 |

### Invoice workflow (`tool-use/t1_orchestrate`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $3.19 | $2.74–$3.64 | $3.51 | 6.2 | 6.2 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $1.97 | $1.74–$2.20 | $2.00 | 16.7 | 16.7 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $3.20 | $1.91–$5.16 | $2.58 | 10.7 | 10.6 | 1 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $3.99 | $3.66–$4.34 | $4.09 | 6.7 | 6.6 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $63.95 | $55.52–$74.51 | $114.08 | 12.6 | 12.5 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $565.37 | $526.38–$623.04 | $176.36 | 6.4 | 6.3 | 0 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $75.34 | $59.91–$96.83 | $58.49 | 8.9 | 8.8 | 1 / 0 |
| `ds41-openrouter` | low | 10/10 | $59.36 | $47.98–$72.74 | $111.38 | 13.2 | 13.1 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $84.74 | $69.37–$101.60 | $70.40 | 13.5 | 13.4 | 0 / 0 |
| `dspro-openrouter` | low | 10/10 | $525.22 | $512.01–$535.70 | $129.09 | 5.9 | 5.9 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $980.70 | $979.80–$981.60 | $985.36 | 12.7 | 12.7 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $124.00 | $120.36–$126.84 | $125.83 | 7.2 | 7.2 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $2086.16 | $2059.89–$2111.06 | $2085.29 | 8.4 | 8.3 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $4372.05 | $4089.94–$4770.23 | $4378.21 | 13.9 | 13.9 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $4570.90 | $4400.08–$4744.30 | $4802.50 | 11.8 | 11.8 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $12229.77 | $11207.03–$13265.68 | $12946.64 | 20.5 | 20.5 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $3.51 | $2.84–$4.54 | $3.21 | 7.0 | 7.0 | 0 / 0 |
| `glm53-lunaroute` | high | 10/10 | $2.30 | $2.06–$2.55 | $2.35 | 9.6 | 9.6 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $2.36 | $2.18–$2.56 | $2.18 | 11.7 | 11.7 | 0 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $4.71 | $4.11–$5.41 | $4.22 | 10.0 | 10.0 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $69.20 | $57.51–$81.86 | $115.45 | 13.8 | 13.7 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $594.35 | $541.73–$667.24 | $180.98 | 6.3 | 6.2 | 0 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $70.09 | $66.25–$75.79 | $64.12 | 10.6 | 10.5 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $69.70 | $57.14–$84.16 | $124.48 | 13.9 | 13.8 | 0 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $94.29 | $82.45–$107.70 | $76.27 | 16.9 | 16.9 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $572.62 | $541.46–$606.33 | $210.57 | 6.4 | 6.4 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $1018.08 | $991.89–$1044.00 | $1052.38 | 12.9 | 12.8 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $130.57 | $128.66–$133.57 | $130.89 | 8.3 | 8.2 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $2090.69 | $2043.83–$2171.44 | $2171.38 | 8.2 | 8.1 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $5423.04 | $5076.23–$5657.42 | $5340.83 | 15.8 | 15.8 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $5310.10 | $5106.79–$5498.00 | $5351.00 | 13.8 | 13.8 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $12326.30 | $11266.90–$13427.15 | $14138.79 | 20.6 | 20.5 | 0 / 0 |

### Account unlock workflow (`tool-use/t2_toolselect`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $2.81 | $2.76–$2.88 | $2.88 | 4.0 | 4.0 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $2.15 | $2.15–$2.16 | $2.15 | 6.2 | 6.1 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $2.16 | $2.15–$2.17 | $2.16 | 8.2 | 8.1 | 0 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $3.75 | $3.73–$3.78 | $3.75 | 5.5 | 5.4 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $43.77 | $40.87–$46.08 | $70.56 | 8.9 | 8.8 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $417.01 | $366.78–$463.68 | $333.43 | 7.8 | 7.7 | 0 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $37.66 | $37.60–$37.72 | $37.75 | 6.6 | 6.6 | 0 / 0 |
| `ds41-openrouter` | low | 10/10 | $45.28 | $41.48–$50.68 | $74.08 | 8.9 | 8.8 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $62.70 | $50.77–$75.51 | $30.96 | 14.0 | 13.9 | 0 / 0 |
| `dspro-openrouter` | low | 10/10 | $357.45 | $297.16–$423.66 | $356.04 | 8.4 | 8.4 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $768.06 | $764.16–$772.34 | $766.50 | 9.3 | 9.3 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $113.50 | $111.82–$115.10 | $113.64 | 5.8 | 5.8 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $2285.93 | $2277.85–$2294.63 | $2287.07 | 8.5 | 8.5 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $4593.43 | $4567.68–$4617.06 | $4577.60 | 16.4 | 16.3 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $3869.50 | $3843.49–$3896.00 | $3856.20 | 11.0 | 11.0 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $11542.76 | $11511.73–$11575.37 | $11554.99 | 10.5 | 10.5 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $2.85 | $2.82–$2.87 | $2.88 | 4.4 | 4.4 | 0 / 0 |
| `glm53-lunaroute` | high | 10/10 | $2.26 | $2.21–$2.32 | $2.23 | 9.0 | 8.9 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $2.23 | $2.15–$2.29 | $2.27 | 12.5 | 12.4 | 0 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $3.93 | $3.88–$4.00 | $4.00 | 4.1 | 4.1 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $45.45 | $42.36–$48.56 | $80.94 | 8.7 | 8.7 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $486.72 | $429.16–$559.92 | $357.03 | 8.2 | 8.2 | 0 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $38.89 | $38.07–$39.78 | $38.48 | 6.7 | 6.6 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $47.65 | $42.81–$54.03 | $76.65 | 9.0 | 8.9 | 0 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $61.84 | $49.23–$74.89 | $30.72 | 14.9 | 14.8 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $400.76 | $333.73–$478.24 | $331.74 | 8.5 | 8.4 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $768.32 | $764.32–$772.18 | $767.02 | 11.0 | 11.0 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $114.89 | $113.87–$115.98 | $114.14 | 6.2 | 6.2 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $2299.14 | $2294.50–$2303.83 | $2291.14 | 8.9 | 8.8 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $4622.84 | $4603.18–$4640.19 | $4649.60 | 15.5 | 15.5 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $3888.10 | $3856.89–$3918.41 | $4564.00 | 10.9 | 10.8 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $12018.24 | $11801.52–$12199.60 | $12037.76 | 11.6 | 11.5 | 0 / 0 |

### Inventory workflow (`tool-use/t3_inventory`)

| Starting route | Effort | Passes | Measured / 100K attempts and successes | 95% cost interval | Frozen estimate / 100K | Wall seconds | Active seconds | Retries / upgrades |
|---|---|---:|---:|---|---:|---:|---:|---:|
| `ds41-lunaroute` | low | 10/10 | $3.32 | $3.15–$3.47 | $3.40 | 6.3 | 6.3 | 0 / 0 |
| `glm53-lunaroute` | low | 10/10 | $2.06 | $2.00–$2.13 | $1.96 | 7.4 | 7.4 | 0 / 0 |
| `glm53-flash-lunaroute` | low | 10/10 | $2.10 | $2.01–$2.25 | $2.14 | 10.5 | 10.4 | 0 / 0 |
| `muse-spark-open-lunaroute` | low | 10/10 | $5.10 | $4.79–$5.40 | $5.04 | 7.8 | 7.8 | 0 / 0 |
| `ds41-openrouter-floor` | low | 10/10 | $268.46 | $242.51–$297.33 | $164.24 | 7.4 | 7.4 | 0 / 0 |
| `dspro-openrouter-floor` | low | 10/10 | $807.66 | $756.29–$875.67 | $233.81 | 8.0 | 8.0 | 0 / 0 |
| `gpt6-luna-direct` | low | 10/10 | $68.07 | $62.71–$72.88 | $65.99 | 10.4 | 10.3 | 0 / 0 |
| `ds41-openrouter` | low | 10/10 | $268.30 | $247.16–$288.75 | $166.83 | 7.1 | 7.0 | 0 / 0 |
| `ds41-1017-openrouter` | low | 10/10 | $81.68 | $73.06–$90.42 | $62.74 | 14.1 | 14.1 | 0 / 0 |
| `dspro-openrouter` | low | 10/10 | $744.63 | $703.84–$788.88 | $261.95 | 7.7 | 7.6 | 0 / 0 |
| `gpt61-sol-direct` | low | 10/10 | $1135.58 | $1073.97–$1209.97 | $1142.42 | 13.2 | 13.1 | 0 / 0 |
| `claude-haiku55-openrouter` | low | 10/10 | $172.05 | $171.64–$172.43 | $172.97 | 8.6 | 8.5 | 0 / 0 |
| `claude-sonnet55-openrouter` | low | 10/10 | $2676.75 | $2656.43–$2694.51 | $2678.69 | 8.2 | 8.2 | 0 / 0 |
| `claude-opus55-openrouter` | low | 10/10 | $5393.24 | $5375.64–$5411.81 | $5374.89 | 14.1 | 14.0 | 0 / 0 |
| `gpt6-astra-direct` | low | 10/10 | $5864.48 | $5467.71–$6259.27 | $5789.18 | 12.9 | 12.9 | 0 / 0 |
| `claude-fable51-openrouter` | low | 10/10 | $16364.32 | $16282.13–$16426.57 | $16176.74 | 15.4 | 15.4 | 0 / 0 |
| `ds41-lunaroute` | high | 10/10 | $3.31 | $3.13–$3.45 | $3.40 | 6.6 | 6.5 | 0 / 0 |
| `glm53-lunaroute` | high | 10/10 | $2.31 | $2.23–$2.40 | $2.26 | 12.6 | 12.5 | 0 / 0 |
| `glm53-flash-lunaroute` | high | 10/10 | $2.21 | $2.15–$2.28 | $2.26 | 14.9 | 14.8 | 0 / 0 |
| `muse-spark-open-lunaroute` | high | 10/10 | $5.86 | $5.40–$6.38 | $6.12 | 9.2 | 9.1 | 0 / 0 |
| `ds41-openrouter-floor` | high | 10/10 | $287.03 | $256.86–$315.28 | $169.83 | 7.1 | 7.1 | 0 / 0 |
| `dspro-openrouter-floor` | high | 10/10 | $879.73 | $758.95–$1038.22 | $340.49 | 8.1 | 8.0 | 0 / 0 |
| `gpt6-luna-direct` | high | 10/10 | $67.60 | $65.83–$69.49 | $69.85 | 10.3 | 10.3 | 0 / 0 |
| `ds41-openrouter` | high | 10/10 | $290.36 | $271.15–$309.32 | $165.74 | 6.9 | 6.8 | 0 / 0 |
| `ds41-1017-openrouter` | high | 10/10 | $91.42 | $75.77–$108.20 | $69.02 | 17.1 | 17.1 | 0 / 0 |
| `dspro-openrouter` | high | 10/10 | $799.97 | $764.49–$847.00 | $432.59 | 8.1 | 8.0 | 0 / 0 |
| `gpt61-sol-direct` | high | 10/10 | $1213.31 | $1143.83–$1281.94 | $1268.32 | 15.1 | 15.1 | 0 / 0 |
| `claude-haiku55-openrouter` | high | 10/10 | $182.68 | $179.41–$186.04 | $180.18 | 9.5 | 9.4 | 0 / 0 |
| `claude-sonnet55-openrouter` | high | 10/10 | $2894.94 | $2784.17–$3034.54 | $2900.85 | 9.0 | 9.0 | 0 / 0 |
| `claude-opus55-openrouter` | high | 10/10 | $6749.09 | $6698.61–$6798.24 | $6778.84 | 16.7 | 16.6 | 0 / 0 |
| `gpt6-astra-direct` | high | 10/10 | $6579.32 | $6277.18–$6845.19 | $6628.23 | 14.4 | 14.3 | 0 / 0 |
| `claude-fable51-openrouter` | high | 10/10 | $17008.71 | $16940.62–$17086.02 | $17172.23 | 16.9 | 16.9 | 0 / 0 |

## Measured conditional stage results

Reach counts original workflows that reached a model. Base passes and Aegis recoveries are separate. The interval uses reached workflows only. Cost contribution uses all ten original workflows as the denominator, not reached workflows.

The table lists every reached stage. Zero-reach stages have no measured pass rate. They remain in the frozen manifest but are omitted here. Stage samples from different starting routes are separate. Do not treat them as independent model evaluations.

### Long tiling proof

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 2 | 8 | 1 | 3/10 | 10.8%–60.3% | $3.85 |
| `ds41-lunaroute` | low | `glm53-flash-lunaroute` | 7 | 5 | 2 | 1 | 6/7 | 48.7%–97.4% | $0.57 |
| `ds41-lunaroute` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $114.38 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 8 | 2 | 2 | 10/10 | 72.2%–100.0% | $0.83 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 8 | 2 | 2 | 10/10 | 72.2%–100.0% | $0.71 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.96 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 3 | 7 | 5 | 8/10 | 49.0%–94.3% | $292.39 |
| `ds41-openrouter-floor` | low | `glm53-flash-lunaroute` | 2 | 1 | 1 | 0 | 1/2 | 9.5%–90.5% | $0.24 |
| `ds41-openrouter-floor` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $104.48 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 0 | 10 | 0 | 0/10 | 0.0%–27.8% | $3660.20 |
| `dspro-openrouter-floor` | low | `glm53-flash-lunaroute` | 10 | 4 | 6 | 5 | 9/10 | 59.6%–98.2% | $1.12 |
| `dspro-openrouter-floor` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $105.18 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $66.53 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 8 | 2 | 1 | 9/10 | 59.6%–98.2% | $169.27 |
| `ds41-openrouter` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $105.18 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 0 | 10 | 5 | 5/10 | 23.7%–76.3% | $455.15 |
| `ds41-1017-openrouter` | low | `glm53-flash-lunaroute` | 5 | 4 | 1 | 0 | 4/5 | 37.6%–96.4% | $0.34 |
| `ds41-1017-openrouter` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $104.58 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 0 | 10 | 1 | 1/10 | 1.8%–40.4% | $2681.05 |
| `dspro-openrouter` | low | `glm53-flash-lunaroute` | 9 | 4 | 5 | 4 | 8/9 | 56.5%–98.0% | $0.99 |
| `dspro-openrouter` | low | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $106.48 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1030.30 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $99.00 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 8 | 2 | 2 | 10/10 | 72.2%–100.0% | $1350.97 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2509.21 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5269.00 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4879.38 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 0 | 10 | 0 | 0/10 | 0.0%–27.8% | $4.48 |
| `ds41-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 5 | 5 | 3 | 8/10 | 49.0%–94.3% | $1.63 |
| `ds41-lunaroute` | high | `gpt61-sol-direct` | 2 | 2 | 0 | 0 | 2/2 | 34.2%–100.0% | $357.56 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 5 | 5 | 3 | 8/10 | 49.0%–94.3% | $2.24 |
| `glm53-lunaroute` | high | `glm53-flash-lunaroute` | 2 | 1 | 1 | 1 | 2/2 | 34.2%–100.0% | $0.27 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 5 | 5 | 4 | 9/10 | 59.6%–98.2% | $1.45 |
| `glm53-flash-lunaroute` | high | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $178.48 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 0 | 10 | 5 | 5/10 | 23.7%–76.3% | $4.47 |
| `muse-spark-open-lunaroute` | high | `glm53-flash-lunaroute` | 5 | 4 | 1 | 1 | 5/5 | 56.6%–100.0% | $0.72 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 0 | 10 | 6 | 6/10 | 31.3%–83.2% | $409.10 |
| `ds41-openrouter-floor` | high | `glm53-flash-lunaroute` | 4 | 3 | 1 | 1 | 4/4 | 51.0%–100.0% | $0.45 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 0 | 10 | 0 | 0/10 | 0.0%–27.8% | $4200.27 |
| `dspro-openrouter-floor` | high | `glm53-flash-lunaroute` | 10 | 5 | 5 | 3 | 8/10 | 49.0%–94.3% | $1.74 |
| `dspro-openrouter-floor` | high | `gpt61-sol-direct` | 2 | 2 | 0 | 0 | 2/2 | 34.2%–100.0% | $373.46 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 4 | 6 | 3 | 7/10 | 39.7%–89.2% | $323.66 |
| `gpt6-luna-direct` | high | `glm53-flash-lunaroute` | 3 | 2 | 1 | 0 | 2/3 | 20.8%–93.9% | $0.49 |
| `gpt6-luna-direct` | high | `gpt61-sol-direct` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $165.68 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 5 | 5 | 2 | 7/10 | 39.7%–89.2% | $253.33 |
| `ds41-openrouter` | high | `glm53-flash-lunaroute` | 3 | 2 | 1 | 1 | 3/3 | 43.9%–100.0% | $0.35 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 5 | 5 | 3 | 8/10 | 49.0%–94.3% | $309.68 |
| `ds41-1017-openrouter` | high | `glm53-flash-lunaroute` | 2 | 1 | 1 | 1 | 2/2 | 34.2%–100.0% | $0.38 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 0 | 10 | 1 | 1/10 | 1.8%–40.4% | $2755.98 |
| `dspro-openrouter` | high | `glm53-flash-lunaroute` | 9 | 6 | 3 | 3 | 9/9 | 70.1%–100.0% | $1.18 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1770.20 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 7 | 3 | 2 | 9/10 | 59.6%–98.2% | $250.54 |
| `claude-haiku55-openrouter` | high | `glm53-flash-lunaroute` | 1 | 1 | 0 | 0 | 1/1 | 20.7%–100.0% | $0.07 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1375.61 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2896.82 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $8491.50 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $7670.38 |

### Expected flips

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.25 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.21 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.16 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.43 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $32.20 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1029.49 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $16.96 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $52.29 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $33.59 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $305.60 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $278.10 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $25.05 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $460.09 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1187.30 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1339.50 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2217.08 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.26 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.28 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.27 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.75 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $30.44 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1069.96 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $17.86 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $53.12 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $31.51 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $607.07 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $335.60 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $42.09 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $493.11 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1743.91 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1928.00 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2346.85 |

### Die expectation

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.24 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.23 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.20 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.40 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $28.61 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $801.92 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $15.85 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $57.15 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $30.19 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $352.18 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $398.60 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $31.99 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $426.22 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1573.85 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1875.00 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2551.52 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $0.36 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.31 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $0.44 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.83 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $31.13 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1364.79 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $17.63 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 8 | 2 | 2 | 10/10 | 72.2%–100.0% | $132.49 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $32.62 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $306.55 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $537.40 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $42.15 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $455.44 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1850.89 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2883.00 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3173.97 |

### Catalan count

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.67 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.25 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.19 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.46 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $59.16 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $4471.44 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $18.43 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $80.56 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $77.07 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2453.43 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $382.80 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $34.45 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $667.39 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1770.92 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2048.00 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3023.10 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1.01 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.62 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $0.39 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1.25 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $93.34 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 1 | 9 | 9 | 10/10 | 72.2%–100.0% | $7971.43 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $36.05 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $99.53 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $97.70 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4927.96 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $780.00 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $74.29 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $672.77 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2115.49 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3925.00 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4078.63 |

### Invoice workflow

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.19 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1.97 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $3.20 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.99 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $63.95 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $565.37 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 9 | 1 | 1 | 10/10 | 72.2%–100.0% | $75.34 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $59.36 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $84.74 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $525.22 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $980.70 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $124.00 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2086.16 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4372.05 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4570.90 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $12229.77 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.51 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.30 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.36 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4.71 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $69.20 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $594.35 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $70.09 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $69.70 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $94.29 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $572.62 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1018.08 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $130.57 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2090.69 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5423.04 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5310.10 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $12326.30 |

### Account unlock workflow

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.81 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.15 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.16 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.75 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $43.77 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $417.01 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $37.66 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $45.28 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $62.70 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $357.45 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $768.06 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $113.50 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2285.93 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4593.43 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3869.50 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $11542.76 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.85 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.26 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.23 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.93 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $45.45 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $486.72 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $38.89 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $47.65 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $61.84 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $400.76 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $768.32 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $114.89 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2299.14 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $4622.84 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3888.10 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $12018.24 |

### Inventory workflow

| Starting route | Effort | Reached model | Reached | Base passes | Aegis retries | Aegis recoveries | Stage passes | 95% conditional pass interval | Cost contribution / 100K originals |
|---|---|---|---:|---:|---:|---:|---:|---|---:|
| `ds41-lunaroute` | low | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.32 |
| `glm53-lunaroute` | low | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.06 |
| `glm53-flash-lunaroute` | low | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.10 |
| `muse-spark-open-lunaroute` | low | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5.10 |
| `ds41-openrouter-floor` | low | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $268.46 |
| `dspro-openrouter-floor` | low | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $807.66 |
| `gpt6-luna-direct` | low | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $68.07 |
| `ds41-openrouter` | low | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $268.30 |
| `ds41-1017-openrouter` | low | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $81.68 |
| `dspro-openrouter` | low | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $744.63 |
| `gpt61-sol-direct` | low | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1135.58 |
| `claude-haiku55-openrouter` | low | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $172.05 |
| `claude-sonnet55-openrouter` | low | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2676.75 |
| `claude-opus55-openrouter` | low | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5393.24 |
| `gpt6-astra-direct` | low | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5864.48 |
| `claude-fable51-openrouter` | low | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $16364.32 |
| `ds41-lunaroute` | high | `ds41-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $3.31 |
| `glm53-lunaroute` | high | `glm53-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.31 |
| `glm53-flash-lunaroute` | high | `glm53-flash-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2.21 |
| `muse-spark-open-lunaroute` | high | `muse-spark-open-lunaroute` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $5.86 |
| `ds41-openrouter-floor` | high | `ds41-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $287.03 |
| `dspro-openrouter-floor` | high | `dspro-openrouter-floor` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $879.73 |
| `gpt6-luna-direct` | high | `gpt6-luna-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $67.60 |
| `ds41-openrouter` | high | `ds41-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $290.36 |
| `ds41-1017-openrouter` | high | `ds41-1017-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $91.42 |
| `dspro-openrouter` | high | `dspro-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $799.97 |
| `gpt61-sol-direct` | high | `gpt61-sol-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $1213.31 |
| `claude-haiku55-openrouter` | high | `claude-haiku55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $182.68 |
| `claude-sonnet55-openrouter` | high | `claude-sonnet55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $2894.94 |
| `claude-opus55-openrouter` | high | `claude-opus55-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $6749.09 |
| `gpt6-astra-direct` | high | `gpt6-astra-direct` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $6579.32 |
| `claude-fable51-openrouter` | high | `claude-fable51-openrouter` | 10 | 10 | 0 | 0 | 10/10 | 72.2%–100.0% | $17008.71 |

## Limits

- Seven fixed tasks are not a broad quality benchmark. Repetition does not test unseen-task coverage.
- Descriptive Wilson intervals assume independent trials. Caching and shared service conditions can violate that assumption.
- Bootstrap intervals use 1,000 workflow resamples. Configuration intervals include task-mix variation. They can miss rare future upgrades. They do not include future prices, the unknown timeout charge, or LunaRoute throughput error.
- Ten repeats per task are small samples. A 10/10 result does not prove perfect reliability. Selection on the same older task set limits generalization.
- There is no plain-retry control. A recovery does not show that Aegis caused it.
- The greedy rule optimizes estimated cost. It is not proven globally optimal. It does not optimize latency.
- Tiling and each tool request allow 4,096 output tokens. The other reasoning tasks allow 8,192. Tool attempts allow twelve model requests and 32 tool calls. Base and retry limits match.
- Terminal models did not fail in this run. That does not guarantee future success.
- Offline checks and unit tests do not establish user preference or safe production routing.

## Public evidence

- [Interactive report](https://eranshir.github.io/bench3/economics/#linked-ladder)
- [All measured statistics](summary.json)
- [All task/effort/starting-route costs](TASK_ECONOMICS.csv)
- [Frozen plans and source hashes](manifest.json)
- [Main final audit](final_audit.json)
- [Strict signed-journal audit](journal_audit.json)
- [Approved timeout recovery](recovery_audit.json)
- [Retained 2,100-task training report](../../campaigns/20261017T101248Z-objective-k10/FINAL_REPORT.md)
- [140-task DeepSeek 1017 training report](../../campaigns/20261017T131926Z-ds41-1017-k10/FINAL_REPORT.md)

All ten proofs are in `checkpoints/round-01-verification.json` through `checkpoints/round-10-verification.json`. Private sessions, request intents, signing keys, and raw chain records are not public.
