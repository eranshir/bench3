# Economic route benchmark

This study answers one question:

> For a given task, what does one attempt and one successful result cost on
> each model and provider route?

The study is separate from the historical `bench3` result files. Reasoning
keeps the original tasks and graders under `economics/results/`. Tool-use
now executes local tools and checks their final state under
`economics/toolloop/`.

## What is compared

The unit under test is a **route**, not only a model. A route combines:

- the model family;
- the provider endpoint;
- the reasoning effort;
- the billing method;
- the provider price at the run time.

This distinction is required for comparisons such as:

- DeepSeek V4.1 Flash through OpenRouter;
- DeepSeek V4.1 Flash through LunaRoute;
- DeepSeek V4 Pro 0813 through OpenRouter;
- GLM 5.3, GLM 5.3 Flash, and Muse Spark Open through LunaRoute;
- Claude models through OpenRouter;
- GPT-6.1 Sol through the OpenAI API.

DeepSeek and Claude runs use OpenRouter. GPT runs use the direct OpenAI
Responses API.

## Cost views

### Fresh linked ladder benchmark

`run_ladder.py` freezes the 224 task/effort/starting-route plans from the
audited 2,240 training observations. It then runs 2,240 fresh original
workflows: 16 starting routes, seven tasks, two efforts, and ten repetitions.
New repetition IDs 1–10 belong only to this separate campaign. They are
not the older pilot or a copy of training records.

Each reached model gets the original task with fresh tool state. A base
failure triggers one fully enforced Aegis retry with that model. A second
failure permits the next frozen model. An objective pass stops the chain.
The final model can fail; the runner records that result without extending
the plan. Provider errors do not authorize upgrades. A persisted uncertain
request blocks automatic resubmission. Completed stage records are reused
only to resume that same new chain, never across chains.

For the approved DeepSeek 1017 support-workflow timeout in repetition 7,
`continue_ladder_tool.py` reconstructs the saved conversation through local
deterministic replay. It does not send the three completed requests again.
The timed-out fourth request consumes one of the original twelve slots.
At most eight further provider requests are allowed; the output and tool
limits stay unchanged. The original timeout and partial artifacts remain
intact. Returned receipts are counted once, and the missing timeout charge
stays unknown, not zero. `recovery_audit.json` records the continuation.
That workflow's wall time includes the pause for human approval. Its active
model/workflow time does not include that approval wait.

The existing token limits, executed tools, graders, full method payload,
plan/completion/closure gates, and signed journals stay unchanged. The
runner rechecks the retry journal and method gates before each upgrade.
`verify_ladder.py` independently replays every grade and journal, verifies
all paths and ten round proofs, and reconciles every stage cost.

The required additional `audit_ladder_evidence.py` audit checks the actual
adapter run directory. A reasoning record's `local_ir_dir` ends in `.am`;
its signed journal is in the parent run directory's `evidence-state`.
The older audit helper can use the wrong empty state directory. The retry
adapter itself verifies the correct nonempty journal when it creates the
record. The extra audit requires a nonempty saved journal and exact matching
head, segment, journal identity, public-key identity, and method gates.
It makes no provider calls. Both audits must pass before publication.

```bash
cd bench3/economics
python3 run_ladder.py --status
python3 run_ladder.py --resume --campaign ladder_campaigns/EXACT_CAMPAIGN_ID
python3 verify_ladder.py --campaign ladder_campaigns/EXACT_CAMPAIGN_ID --save
python3 audit_ladder_evidence.py --campaign ladder_campaigns/EXACT_CAMPAIGN_ID --save
```

Use `--launch` only for a newly authorized run. Do not restart a new campaign
to replace a low score or repeat completed provider calls.

`ladder_data.js` contains only public aggregates. It updates after each
completed chain. The local report refreshes it every 15 seconds. It shows
fresh sample counts, cost per 100,000 original attempts and successes,
Wilson pass intervals, bootstrap cost intervals, actual stage reach,
recovery and upgrade counts, and wall time. Earlier estimates remain
separate and frozen. Live costs cover completed chains only. In-progress
or interrupted requests need later reconciliation.

The new public report has a separate measured-ladder section. Its CSV and
JSON contain all 224 task/effort/starting-route cells. Private chain records,
provider responses, process state, and evidence signing keys stay local.

The measured cost-versus-time chart compares starting routes. Its task and
effort filters use fresh linked observations only. Both efforts appear as
separate points. All-task points use the saved pooled configuration median;
they do not average task medians. Cost uses dollars per 100,000 original
workflows on a logarithmic axis. Time uses a linear axis with full wall time
as the default. Active attempt time is also available. Point selection shows
sample counts, cost and pass intervals, retries, and upgrades. The chart
does not change benchmark evidence or call a model.

```bash
python3 -m unittest test_continue_ladder_tool.py test_ladder.py test_campaign.py test_economics.py test_toolloop.py test_extension.py
node test_hybrid.js
node test_ladder_report.js
node test_ladder_scatter.js
node test_report_ui.js
```

### Aegis-first hybrid and greedy cost ladder

The report separates four policies:

1. Base only: measured base attempts, with no retry or model upgrade.
2. Aegis only: measured base attempts plus one enforced retry per failure.
3. Aegis then fallback: the measured Aegis policy, then an estimated model upgrade for tasks that still fail.
4. Aegis cost ladder: estimated successive model levels, with one failure-only Aegis retry at each reached model.

`hybrid = mean base-plus-Aegis cost + (1 − after-Aegis pass ratio) × fallback cost`

The mean cost includes all base attempts and all recorded retries, divided
by the original task count. Failed attempts are paid. All policy estimates
use 100,000 original tasks, not 100,000 successful tasks. The fallback is
the cheapest route for that task and effort among routes that passed all
140 objective base tasks: seven tasks, both efforts, and ten repetitions.
Partial runs, coding pilot scores, and Aegis recoveries do not qualify a
fallback. A stage requires all ten base observations and every required
retry. An incomplete stage produces no policy estimate.

The greedy ladder chooses the next model by the lowest stage cost divided
by its after-Aegis task pass ratio. Each upgrade must have a higher observed
pass ratio. A reverse savings check removes levels that do not reduce the
estimated remaining cost. The ladder ends at a fully qualified fallback.
Its cost is `sum(estimated reach × full stage cost)`. A stage with 10/10
passes gives later stages zero estimated reach, but keeps the final fallback
in the plan. This is not proof of perfect reliability or a globally optimal
policy. Latency is not part of the score.

These estimated views do not use the fresh linked results. They use marginal pass rates from
separately tested models. Failures can correlate across models. The cost
of a model on upstream failures can differ from its observed mean cost.
Selection and scoring use the same small sample. Actual cascade costs can
therefore be higher. No combined measured pass rate or policy confidence
interval is claimed.

The CSV also keeps the original requested formula
`p × base cost + (1 − p) × fallback cost`, with the base pass ratio `p`.
That weighted estimate omits failed cheap attempts and Aegis retries. It
is not the hybrid bill shown in the report. The CSV includes base-first
escalation, Aegis-first escalation, and ladder costs and paths.

`hybrid_cost.js` computes these values from the report data. It does not
call models, change grades, or change the frozen benchmark. The campaign
summary's hybrid column is the equal-task mean of the task-level estimates,
not a new estimate from a pooled pass ratio. “Both efforts” averages
separately calculated low/high policies.

```bash
node bench3/economics/test_hybrid.js
node bench3/economics/test_report_ui.js
```

Token-billed routes report two cost values:

1. `inference_cost_usd`: the posted token cost.
2. `cash_cost_usd`: the inference cost plus a route-level credit fee, when one
   applies. OpenRouter Standard credit purchases add 5.5%.

LunaRoute uses a fixed monthly lane plan. The benchmark reports:

1. `marginal_cost_usd`: zero for an additional included request;
2. `capacity_allocated_cost_usd`: the task's share of the plan cost at a stated
   monthly token volume;
3. break-even monthly task counts against token-billed routes.

The LunaRoute capacity model uses the observed rule supplied for this study:
4 billion tokens per 24 hours on a $500 monthly 10-priority / 40-total lane
plan. The account is assumed to run at full capacity for 30 days. This is 120
billion tokens per month and about $0.00417 per million tokens.

OpenRouter single-shot records include the upstream provider and its reported
inference charge. A catalog estimate is kept as a check because default
routing can select a higher-priced provider. Agent runs use a catalog or
advertised-floor estimate when the generation receipt endpoint does not return
the per-call receipts.

## Current route list

`routes.yaml` is the dated source of truth. It includes current OpenAI,
Anthropic, DeepSeek, OpenRouter, and LunaRoute routes. Historical `arms.yaml`
entries remain unchanged so old results keep their original meaning.

## Ten new repetitions

### Pinned DeepSeek 1017 extension

The October 17 extension adds `deepseek/deepseek-v4.1-flash-1017` through
OpenRouter. It runs only that new route. The seven tasks, low/high effort,
ten repetitions, output limits, graders, and full enforced Aegis failure
retries stay unchanged. The extension has 140 new base tasks.

The report retains the completed 2,100-task baseline. It reads the two
campaigns separately; it does not copy or relabel old observations as new
runs. A complete comparison has 2,240 base tasks across 16 routes. The
baseline ran earlier. The report states this limit on the comparison.

To start a newly authorized extension:

```bash
cd bench3/economics
python3 extend_campaign.py \
  --baseline campaigns/20261017T101248Z-objective-k10 \
  --route ds41-1017-openrouter
```

The extension checks baseline source hashes, route settings, and the final
baseline audit before it starts. It rejects an old route as a new route.
The final audit checks the exact declared matrix; it supports both the
original 2,100-task campaign and the 140-task extension.

### Original campaign

`run_campaign.py` runs the current objective matrix ten more times. Each
repetition has 15 routes, two effort levels, and seven tasks: four reasoning
tasks and three executed tool workflows. The campaign has 2,100 base tasks.
The coding pilot is separate. Pilot repetition 1 is not part of these
statistics. The new repetition IDs are 2 through 11.

Each failed base task gets one full enforced Aegis retry. The retry uses the
same route, effort, and output limit. Costs for the retry policy include the
failed base task and its retry. A provider connection failure does not count
as a model task failure.

The campaign manifest freezes settings and records source hashes. Tiling
and each tool request allow 4,096 output tokens. The other reasoning tasks
allow 8,192 output tokens. Tool workflows allow at most 12 model requests
and 32 tool calls. Run order is randomized within each repetition.

The active campaign is selected by `campaigns/current.json`. To inspect it:

```bash
cd bench3/economics
python3 run_campaign.py --status
```

To resume the same campaign after an interruption:

```bash
python3 run_campaign.py --resume
```

A process lock prevents two workers from running the same campaign.
Completed tasks are reused; a resume does not replace their records. Use
`--launch` only to start a separate, newly authorized campaign.

The worker publishes `report_data.js` after each completed task. It checks
exact matrix coverage and independently replays grades after each complete
repetition. It then saves a report-data snapshot and verification record in
the campaign's `checkpoints/` folder. `summary.json` and
`TASK_ECONOMICS.csv` contain the current task-level statistics.

Refresh `report.html` once to load the new page code. The page then checks
for new results every 15 seconds. Its task charts show only the new
repetitions. The completed tool pilot and earlier Aegis results have separate
sections. Low and high effort can be selected separately.

Pass rates have 95% Wilson confidence intervals. Task costs use a
1,000-draw percentile bootstrap. A cost interval is not shown for one
observation. Successful-task cost is undefined if no attempt passed. These
intervals describe the repeated fixed tasks. They do not prove a general
model ranking or guarantee statistical significance. Even 10/10 passes has
a Wilson lower bound of about 72% under the independent-trial assumption.

### GitHub report snapshots

The repository contains the benchmark source, configuration, interactive
report, aggregate CSV and JSON reports, and completed round checkpoints.
These files are snapshots from the time of each commit. They do not receive
results from the local worker after a push.

GitHub Pages uses the existing `main` branch and `/docs` folder. After
staging a consistent report and campaign summary, export only the public
assets:

```bash
python3 bench3/economics/export_pages.py --staged
git add docs/economics
```

The published report is at
<https://eranshir.github.io/bench3/economics/>. The export disables local
worker polling and labels an incomplete campaign as a snapshot.

Raw sessions, local workspaces, credentials, private evidence signing keys,
and active process files stay local. They are excluded by `.gitignore`.
Aggregate reports can be read without these private files. To regenerate
them, use the original local records or run a new authorized campaign.

Tests do not call providers:

```bash
python3 -m unittest test_campaign.py test_economics.py test_toolloop.py
```

After completion, run the independent local audit. This command makes no
provider requests. It checks exact matrix coverage, the round snapshots,
all grades, all method gates, and every signed retry journal:

```bash
python3 verify_campaign.py --save
```

The final campaign report is `campaigns/<campaign-id>/FINAL_REPORT.md`.
The audit result is `campaigns/<campaign-id>/final_audit.json`.

## Run the first gate

For tool-use tasks, use the executed tool-loop harness:

```bash
cd bench3/economics
python3 run_toolloop.py --jobs 5 --aegis-on-failure
python3 analyze_toolloop.py
python3 build_report_data.py
```

This runs all 15 enabled routes on three local tool workflows at low and high
effort. Each tool call executes and returns a result to the model. The model
continues until it gives a final answer or reaches the common limit. The
grader replays tool events and checks the final invoice, account, or order
state. Costs include every model request in each workflow.

Failed workflows receive one enforced Aegis retry with fresh tool state.
Records and traces live under `toolloop/`. The current report uses these
executed workflows for the three tool-use tasks. The original one-response
records remain under `results/` for the historical comparison.

OpenAI Responses chains `previous_response_id` with `function_call_output`.
Chat routes retain assistant reasoning fields and return a `tool` message
for each `tool_call_id`. All routes use the same tool schemas and local state
rules. See the official [function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

```bash
cd bench3

python3 economics/run_singleshot.py \
  --route ds41-openrouter \
  --effort high \
  --task reasoning/r2_expectedflips \
  --rep 1

python3 economics/analyze.py
```

Use `--route all` to run all routes that have credentials. Use `--route` more
than once to select a controlled set.

For single-shot reasoning, add `--aegis-on-failure` to retry a graded failure once with the exact
Aegis Method Lite payload in the system prompt. The retry gets its own result
record with `condition: aegis_retry`; it never replaces the base score. For
single-shot reasoning tasks, this is prompt guidance without file or shell enforcement.

The `run_singleshot.py` command now dispatches tool-use tasks to the real
tool-loop runner by default. Its `--aegis-on-failure` option uses the enforced
Aegis adapter for those workflows. Use `--legacy-one-shot-tools` only to
reproduce the earlier one-response contract.

Use the provider-neutral enforced adapter to retry every failed base record
with the full managed Aegis Method payload:

```bash
cd bench3/economics

cargo build --release --bin aegis-method \
  --manifest-path /Users/eranshir/Documents/Projects/mithran/aegis-method/Cargo.toml

python3 aegis_enforced_retry.py --jobs 4
```

The adapter writes `condition: aegis_enforced_retry`. It keeps the original
provider route. It creates `.am` plan, child, and closure contracts. The
official Aegis Method engine blocks execution until the plan passes. The
existing task checker is the falsifier. Completion and closure are denied
when the checker fails. Each retry gets an isolated signed and hash-linked
Aegis evidence journal under `aegis_enforced_runs/`.

This adapter reimplements the provider-neutral control path for the benchmark.
It does not claim native Codex-hook or Claude-hook transport equivalence.

Use the file-sandboxed agent runner for coding tasks:

```bash
python3 economics/run_agentic.py \
  --route ds41-lunaroute \
  --route ds41-openrouter-floor \
  --route claude-sonnet55-openrouter \
  --route gpt61-sol-direct \
  --effort high \
  --task coding/c1_deadlock
```

The runner removes hidden tests and reference files before the model starts.
It also blocks file access to the source repository during the run.
Add `--aegis-on-failure` to give a failed coding task one separate retry. The
runner adds the exact Aegis payload to the harness system prompt. It keeps a
separate session, artifact, cost, and grade record for the retry.

`objective_matrix.yaml` records the first objective task matrix. The runner
accepts repeated `--task` and `--effort` options, so one command can reproduce
the matrix without changing the task definitions. Use `--max-output-tokens`
to test a common output-budget configuration across routes.

## Refresh live catalogs

```bash
python3 economics/refresh_catalog.py
```

This reads the public OpenRouter catalog and all authenticated LunaRoute
catalogs: main, image, embedding, and rerank. It writes a dated snapshot. It
does not change `routes.yaml` automatically because a changed model ID or
price needs review before it can change an experiment.
