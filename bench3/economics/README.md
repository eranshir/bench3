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
