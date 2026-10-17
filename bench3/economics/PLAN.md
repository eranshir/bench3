# Task economics benchmark plan

## Status on 2026-10-17

- The historical objective pilot has 210 runs across 15 routes, seven tasks, and two effort levels.
- The current coding pilot has four routes and one sandboxed task. Each route passed three of four hidden tests.
- GPT-6.1 Sol passed all eight reasoning runs.
- The original tool pilot used a one-response tool-plan contract. It did not execute tool calls or return tool results. Keep those results as history, not as current tool-use evidence.
- The corrected tool pilot completed 90 workflows across 15 routes, three tasks, and two effort levels. All 90 passed. GPT passed 18/18 workflows. The grader replayed the executed tool calls.
- The campaign completed ten new repetitions of all seven objective tasks for each of the 30 route/effort settings. It has 2,100 base tasks: 1,965 passed. All 135 failed tasks received one full enforced Aegis retry; 47 recovered.
- The new OpenRouter slice adds DeepSeek V4 Pro 0813 and the Claude Haiku, Opus, and Fable tiers.
- The real tool-loop gate and the repeated measurement checks are closed for these local tasks. The final audit replayed all 2,235 grades, all 135 signed journals, and 405 method gates. All 900 tool workflows passed. GPT-6.1 Sol passed all 140 base tasks. The coding pilot remains separate.
- The user has authorized one extension: `deepseek/deepseek-v4.1-flash-1017` through OpenRouter. It adds 140 base tasks: seven tasks, low/high effort, and ten repetitions. Each model failure gets one fully enforced Aegis retry. Keep the completed 2,100 baseline observations. Do not repeat their API calls.

## Pinned 1017 extension gate

**User promise:** The user can compare the new pinned snapshot with the completed routes at the same task and budget limits.

**Complete journey:** Run each task at low and high effort ten times -> execute the same tools -> grade the result -> run one enforced retry for each model failure -> audit all new grades, method gates, and journals -> add the new route to the local report -> publish the reviewed report to the existing GitHub Pages site.

**Baseline, metric, and threshold:** Retain the completed 2,100 baseline tasks. Record all 140 new base tasks exactly once. Require ten verified round proofs, a valid enforced retry for every failed base task, and successful final page and data-file checks. Keep all original token and tool limits. Record the upstream provider and returned charge. Show costs per 100,000 tasks, pass intervals, and median time.

**Falsifier:** The pinned route cannot complete the same tool protocol, a grade cannot be reproduced, or an evidence journal is invalid. A low model score is an observed result, not a reason to change the budget or grader.

**Deferrals:** No other new models, no reruns of old routes, no new tasks, and no change to the LunaRoute allocation assumption.

**Stop / Pivot / Continue:** Stop for unresolved access or integrity errors. Fix a local control error only if the task contract stays unchanged. Continue to publication only after the final audit passes. Do not declare a general quality rank or a causal Aegis effect from these fixed tasks.

**Relationships:** Working model access, unchanged task contracts, valid method gates, and a successful audit are verified hard dependencies for this publication. The older baseline is an evidence relationship, not a concurrent control. API spend and provider queues are resource relationships. Extra design work is a preference and does not block the run.

## User and job

The user chooses a model and vendor route for a task. The user needs four values:

- cost per 100,000 attempts;
- pass rate;
- cost per 100,000 successful tasks;
- latency.

The task is the main unit. A vendor plan is one cost input. The study does not try to rank all models with one aggregate score.

## Earliest Testable — real tool journey

**User promise:** A user can compare a real tool task across the 15 enabled routes.

**Complete journey:** Send the prompt -> receive a tool call -> execute the deterministic tool -> return the result -> let the model continue -> grade the final answer -> add all call costs.

**Baseline:** The current harness asks for a complete dependent call sequence in one response. GPT-6.1 Sol returns valid first calls and waits for tool results. This makes the present tool result unsuitable for a general tool-use claim.

**Metric and threshold:** All 15 routes complete the same three tool workflows at low and high effort. Every workflow has a grade, a token record, and a cost record. The grader must reproduce each result from its tool trace. Returned provider receipts must agree with recorded charges within 1% or $0.001, whichever is larger. Disclose interrupted calls with no receipt.

**Falsifier:** A provider needs a different task contract that the harness cannot normalize without changing the user task.

**Deferrals:** New models, more repetitions, subjective writing tasks, a workload calculator, and cloud hosting.

**Observed evidence and decision:** All 90 corrected workflows passed. GPT passed 18/18, compared with 0/18 under the earlier one-response contract. The audit checked 447 returned provider receipts. Three connection resets required fresh-state restarts. Costs include returned receipts from partial workflows. Charges for three interrupted requests remain unknown. Continue to repeated measurement. This closes the harness gate, not a broad model-quality claim.

**Stop / Pivot / Continue:** Stop new model runs if trace replay or cost checks fail. Change a protocol adapter only if the user task stays the same. Continue when all routes complete the same journey and the report states known cost gaps.

## Earliest Usable — full price ladder

**User promise:** A user can choose a route for representative work without builder help.

**Complete journey:** Select a task type -> inspect cost per 100,000 attempts, pass rate, cost per 100,000 successes, and latency -> apply a minimum pass-rate threshold -> choose a route.

**Baseline:** The pilot has one observation per route, task, and effort. That sample cannot establish a stable pass-rate or cost order. The corrected tool pilot is separate from the historical one-response results.

**Model additions:**

- GLM 5.3, GLM 5.3 Flash, and Muse Spark Open through LunaRoute;
- GPT-6 Luna and GPT-6 Astra through the direct OpenAI API;
- Claude Haiku 5.5, Claude Sonnet 5.5, Claude Opus 5.5, and Claude Fable 5.1 through OpenRouter;
- DeepSeek V4 Pro 0813 through OpenRouter, with default and price-first routing.

Keep Claude and DeepSeek on OpenRouter. Keep GPT on the direct OpenAI API.

**LunaRoute catalog decision:**

- Add `glm-5.3-flash` to the main text benchmark. It is a separate live model variant and can change task throughput.
- Keep the four `-background` entries for a saturation and queue test. They are scheduler variants, not new quality models.
- Defer `glm-5.3-vision` and its background variant until the benchmark has image-input tasks.
- Test `clef-flash` and `djev` only in a separate System One decision benchmark. They do not generate normal chat text.
- Exclude `whisper-large-v3` from this benchmark. It is a transcription model.
- Keep image, embedding, and rerank catalogs in the snapshot, but test them only with matching task types.

**Representative slices:**

- short objective reasoning;
- long objective reasoning;
- real tool loop;
- sandboxed coding repair.

**Metric and threshold:** Complete ten new repetitions for every enabled route, task, and effort setting. The matrix contains 15 routes, seven objective tasks, and two effort levels: 2,100 base tasks. Exclude pilot repetition 1; use repetition IDs 2 through 11. Every completed repetition must pass exact coverage and independent grade replay. Every failed base task must have one enforced retry with a valid evidence journal. A passing retry must also pass the method closure gate. An unresolved infrastructure error prevents completion.

**Measurement contract:** Freeze route settings, task files, method files, and runner source in the campaign manifest. Randomize task order within each repetition. Keep base and retry output limits equal: 4,096 tokens for tiling and each tool request; 8,192 tokens for the other reasoning tasks. Tool workflows allow at most 12 model requests and 32 tool calls. Preserve partial receipts after a connection failure. A transport restart is not a model task retry.

**User evidence:** Publish task cost, pass rate, successful-task cost, and median time after each completed task. Save a verified report-data snapshot after each full repetition. Show low and high effort separately. Use 95% Wilson intervals for pass rates and a 1,000-draw percentile bootstrap for task-cost variation. Do not treat a repeated fixed task as a new task sample. Ten repetitions do not guarantee statistical significance or broad model quality.

**Failure intervention:** When a graded base run fails, run one paired retry
with the full enforced Aegis Method. Keep base and retry scores separate.
Report the recovery count and the total base-plus-retry cost and time. A
provider or credential failure does not trigger this intervention because it
is not a model task failure. The earlier Lite condition remains historical.

The enforced follow-up is a separate condition. It uses the full managed
method payload, local `.am` contracts, Aegis Method plan/completion/closure
gates, the existing objective checker as the falsifier, and one isolated
signed Aegis evidence journal per retry. It keeps the original provider route
and records the result as `aegis_enforced_retry`.

**Falsifier:** Trace replay disagrees with a grade, a method journal is invalid, or a task measures provider protocol instead of user outcome. Wide or overlapping intervals can leave a route choice unresolved. That is an evidence limit, not permission to declare a winner.

**Deferrals:** Automatic production routing, broad subjective evaluation, and a workload calculator.

**Stop / Pivot / Continue:** Stop the campaign for an unresolved infrastructure or integrity failure. Diagnose and resume the same campaign without discarding completed records. Change task scope or budgets only in a new declared experiment. After ten verified repetitions, review whether the evidence supports a real route choice. Do not add paid repetitions without a new user request.

## Earliest Lovable — workload decision tool

**User promise:** A user can enter a workload mix and get the lowest-cost route that meets quality and latency limits.

**Complete journey:** Set task shares and volumes -> set minimum pass rate and maximum latency -> view valid routes -> inspect evidence -> export the chosen routing policy.

**Baseline:** The current workflow uses tables and manual comparison.

**Metric and threshold:** The user prefers the tool to the current workflow for two real routing decisions and returns for a later model or price change.

**Falsifier:** The recommendation does not change a real route, capacity, or purchase decision.

**Deferrals:** Automatic route changes and cloud hosting. Keep the first tool local.

**Stop / Pivot / Continue:** Stop if the tool has no decision value. Pivot the workload model when observed use differs from the benchmark. Continue only after observed repeat use or clear preference.

## Cost-policy report slice — Aegis first and greedy model upgrades

**User promise:** Eran can compare the full cost of a failed base task,
an Aegis retry, and later model upgrades without mixing measured costs
with policy estimates.

**Earliest Testable journey:** Select tiling at high effort. Compare base,
Aegis only, Aegis then a qualified fallback, and the greedy ladder. Inspect
each ladder level and export its costs. Baseline: the old weighted estimate
excluded failed cheap attempts and all Aegis retries. Threshold: fixture
arithmetic and all 224 complete task/effort/route cells include every stage
cost; each final fallback passed all 140 base tests; ladder cost does not
exceed direct escalation from the same starting route. Falsifier: an omitted
retry, a partial model used as the final fallback, or an estimate labeled
as an observed handoff. Stop on a false cost or evidence label. Pivot the
heuristic if it adds cost. Continue to the usable gate when checks pass.

**Earliest Usable journey:** Repeat the comparison at both efforts and on
tool tasks. Export all policies and inspect the published report without
builder rescue. Threshold: interaction tests pass, all published links
work, and cost units and policy labels remain clear. Falsifier: an estimate
switch changes the task evidence or mixes effort-specific fallback costs.
Stop for evidence corruption. Pivot unclear controls. Continue only when
the repeated journey is clear. User observation is still needed.

**Earliest Lovable journey:** Eran uses the ladder to choose real model
routes and later returns to it. Baseline: manual cost comparison. Threshold:
two observed routing decisions and later repeat use. Falsifier: the ladder
does not change a decision. Stop if it has no decision value. Pivot if the
estimated handoff costs do not match a later linked test. Continue only
after preference or repeat use is observed.

**Order and deferrals:** Check one complete task journey, then all task
cells, then controls and export, then publication. Do not launch a new paid
linked-ladder campaign as part of a report estimate. Do not claim a measured
combined pass rate, statistical significance, or global cost optimality.
Complete source records, retry costs, and the final integrity audit are hard
dependencies. Later linked tests are evidence relationships. API budget is
a resource relationship. Visual polish is a preference relationship.

## Dependency classification

**Verified hard dependencies:**

- The Usable gate depends on a working real tool loop.
- A valid enforced retry needs working method gates and a valid signed evidence journal.

**Route dependencies:**

- OpenRouter access is verified for the active DeepSeek and Claude routes.
- Two Claude Opus Aegis retries were policy refusals. This is a route-policy limit, not a credential failure.

**Resource relationships:**

- More repetitions use more API budget and run time. This affects batch size, not task order.
- GLM 5.3, GLM 5.3 Flash, and Muse Spark Open need model-specific LunaRoute throughput measurements before the report can assign their fixed-plan cost per task.
- LunaRoute background variants need a sustained-load test. Their lower scheduler priority can change queue time and achieved account throughput.

**Evidence relationships:**

- One repetition cannot establish a stable quality or latency rank.
- Real tool-loop evidence must replace the one-shot tool-plan result before a tool-use claim.
- The repeated task measurements inform a later workload tool. They do not make that tool technically impossible to build sooner.
- Repeated prompts estimate variation on these fixed tasks. They do not establish performance on unseen tasks or prove that an Aegis recovery was caused by the method instead of another attempt.

**Preference relationships:**

- More visual detail and more model tiers can wait until the task-level result changes a real decision.
